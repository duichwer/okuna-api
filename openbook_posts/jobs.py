from django.utils import timezone
from django_rq import job
from video_encoding import tasks
from django.db.models import Q, Count, Max
from django.conf import settings

from openbook_common.utils.model_loaders import get_post_model, get_post_media_model, get_community_model, \
    get_top_post_model, get_post_comment_model, get_moderated_object_model
import logging

logger = logging.getLogger(__name__)


@job
def flush_draft_posts():
    """
    This job should be scheduled
    """
    # Get all draft posts that haven't been modified for a day
    Post = get_post_model()

    draft_posts = Post.objects.filter(status=Post.STATUS_DRAFT,
                                      modified__lt=timezone.now() - timezone.timedelta(days=1)).all()

    flushed_posts = 0

    for draft_post in draft_posts.iterator():
        draft_post.delete()
        flushed_posts = flushed_posts + 1

    return 'Flushed %s posts' % str(flushed_posts)


@job
def process_post_media(post_id):
    Post = get_post_model()
    PostMedia = get_post_media_model()
    post = Post.objects.get(pk=post_id)
    logger.info('Processing media of post with id: %d' % post_id)

    post_media_videos = post.media.filter(type=PostMedia.MEDIA_TYPE_VIDEO)

    for post_media_video in post_media_videos.iterator():
        post_video = post_media_video.content_object
        tasks.convert_video(post_video.file)

    # This updates the status and created attributes
    post._publish()
    logger.info('Processed media of post with id: %d' % post_id)


def _add_post_to_top_post(post):
    TopPost = get_top_post_model()
    if not TopPost.objects.filter(post=post).exists():
        TopPost.objects.create(post=post)


@job
def curate_top_posts():
    """
    This job should be a scheduled repeatable job
    """
    Post = get_post_model()
    Community = get_community_model()
    TopPost = get_top_post_model()
    PostComment = get_post_comment_model()
    ModeratedObject = get_moderated_object_model()
    logger.info('Processing top posts at %s...' % timezone.now())

    top_posts_community_query = Q(community__isnull=False, community__type=Community.COMMUNITY_TYPE_PUBLIC)
    top_posts_community_query.add(Q(is_closed=False, is_deleted=False, status=Post.STATUS_PUBLISHED), Q.AND)
    top_posts_community_query.add(~Q(moderated_object__status=ModeratedObject.STATUS_APPROVED), Q.AND)

    top_posts_criteria_query = Q(total_comments_count__gte=settings.MIN_UNIQUE_TOP_POST_COMMENTS_COUNT) | \
                               Q(reactions_count__gte=settings.MIN_UNIQUE_TOP_POST_REACTIONS_COUNT)

    posts = Post.objects.filter(top_posts_community_query).\
        annotate(total_comments_count=Count('comments__commenter_id'),
                 reactions_count=Count('reactions__reactor_id')).\
        filter(top_posts_criteria_query)

    for post in posts:
        if not post.reactions_count >= settings.MIN_UNIQUE_TOP_POST_REACTIONS_COUNT:
            unique_comments_count = PostComment.objects.filter(post=post).\
                values('commenter_id').\
                annotate(user_comments_count=Count('commenter_id')).count()

            if unique_comments_count >= settings.MIN_UNIQUE_TOP_POST_COMMENTS_COUNT:
                _add_post_to_top_post(post=post)
        else:
            _add_post_to_top_post(post=post)
