from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from auth import require_role
import time

# Simple in-memory cache for posts total count to avoid expensive COUNT queries on high-traffic
POSTS_COUNT_CACHE = {
    'count': None,
    'ts': 0,
    'ttl': 30,  # seconds
}

router = APIRouter(prefix='/api/posts', tags=['Posts'])


@router.get('', response_model=schemas.PostsListOut)
def list_posts(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    # Use cached total when recent
    now = time.time()
    if POSTS_COUNT_CACHE['count'] is None or (now - POSTS_COUNT_CACHE['ts']) > POSTS_COUNT_CACHE['ttl']:
        total = db.query(models.Post).filter(models.Post.is_hidden == False).count()
        POSTS_COUNT_CACHE['count'] = total
        POSTS_COUNT_CACHE['ts'] = now
    else:
        total = POSTS_COUNT_CACHE['count']

    posts = db.query(models.Post).filter(models.Post.is_hidden == False).order_by(models.Post.created_at.desc()).offset(offset).limit(limit).all()
    items = [schemas.PostOut.model_validate(p) for p in posts]
    return schemas.PostsListOut.model_validate({
        'items': items,
        'total': total,
        'offset': offset,
        'limit': limit,
    })


@router.post('', response_model=schemas.PostOut)
def create_post(post: schemas.PostCreate, current_user: models.User = Depends(require_role('VENDOR', 'ADMIN')), db: Session = Depends(get_db)):
    new = models.Post(author_id=current_user.id, title=post.title, body=post.body, image_url=post.image_url)
    db.add(new)
    db.commit()
    db.refresh(new)
    # invalidate count cache
    POSTS_COUNT_CACHE['count'] = None
    return schemas.PostOut.model_validate(new)



@router.get('/admin', response_model=list[schemas.PostOut])
def admin_list_posts(current_user: models.User = Depends(require_role('ADMIN')), db: Session = Depends(get_db)):
    posts = db.query(models.Post).order_by(models.Post.created_at.desc()).all()
    return [schemas.PostOut.model_validate(p) for p in posts]


@router.delete('/{post_id}', response_model=dict)
def delete_post(post_id: int, current_user: models.User = Depends(require_role('ADMIN')), db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(404, 'Post not found')
    # delete likes and comments
    db.query(models.PostLike).filter(models.PostLike.post_id == post_id).delete()
    db.query(models.PostComment).filter(models.PostComment.post_id == post_id).delete()
    db.delete(post)
    db.commit()
    POSTS_COUNT_CACHE['count'] = None
    return {'deleted': True}


@router.patch('/{post_id}/moderate', response_model=schemas.PostOut)
def moderate_post(post_id: int, payload: dict, current_user: models.User = Depends(require_role('ADMIN')), db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(404, 'Post not found')
    is_hidden = payload.get('is_hidden')
    if is_hidden is not None:
        post.is_hidden = bool(is_hidden)
    db.commit()
    db.refresh(post)
    POSTS_COUNT_CACHE['count'] = None
    return schemas.PostOut.model_validate(post)


@router.delete('/{post_id}/comments/{comment_id}', response_model=dict)
def admin_delete_comment(post_id: int, comment_id: int, current_user: models.User = Depends(require_role('ADMIN')), db: Session = Depends(get_db)):
    c = db.query(models.PostComment).filter(models.PostComment.id == comment_id, models.PostComment.post_id == post_id).first()
    if not c:
        raise HTTPException(404, 'Comment not found')
    db.delete(c)
    # decrement post comments_count if possible
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post and post.comments_count:
        post.comments_count = max(0, post.comments_count - 1)
    db.commit()
    return {'deleted': True}



@router.post('/{post_id}/like')
def toggle_like(post_id: int, current_user: models.User = Depends(require_role('CUSTOMER','VENDOR','DRIVER','ADMIN')), db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(404, 'Post not found')
    existing = db.query(models.PostLike).filter(models.PostLike.post_id==post_id, models.PostLike.user_id==current_user.id).first()
    if existing:
        db.delete(existing)
        post.likes_count = max(0, (post.likes_count or 1) - 1)
        db.commit()
        return {'liked': False, 'likes_count': post.likes_count}
    like = models.PostLike(post_id=post_id, user_id=current_user.id)
    db.add(like)
    post.likes_count = (post.likes_count or 0) + 1
    db.commit()
    return {'liked': True, 'likes_count': post.likes_count}


@router.post('/{post_id}/comments', response_model=schemas.CommentOut)
def create_comment(post_id: int, comment: schemas.CommentCreate, current_user: models.User = Depends(require_role('CUSTOMER','VENDOR','DRIVER','ADMIN')), db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(404, 'Post not found')
    c = models.PostComment(post_id=post_id, user_id=current_user.id, body=comment.body)
    db.add(c)
    post.comments_count = (post.comments_count or 0) + 1
    db.commit()
    db.refresh(c)
    return schemas.CommentOut.model_validate(c)


@router.get('/{post_id}/comments', response_model=list[schemas.CommentOut])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    items = db.query(models.PostComment).filter(models.PostComment.post_id==post_id).order_by(models.PostComment.created_at.asc()).all()
    return [schemas.CommentOut.model_validate(i) for i in items]
