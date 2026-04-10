# Community API for TestMasterProject
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import Post, Comment, Like, Favorite, User
from ..extensions import db
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

community_bp = Blueprint('community', __name__)

# 分类配置
CATEGORIES = [
    {'value': 'experience', 'label': '经验分享', 'color': '#67c23a'},
    {'value': 'question', 'label': '问题求助', 'color': '#f56c6c'},
    {'value': 'resource', 'label': '资源分享', 'color': '#409eff'},
    {'value': 'job', 'label': '求职交流', 'color': '#e6a23c'},
    {'value': 'other', 'label': '其他', 'color': '#909399'}
]

def get_category_info(category_value):
    """获取分类信息"""
    for cat in CATEGORIES:
        if cat['value'] == category_value:
            return cat
    return {'value': category_value, 'label': category_value, 'color': '#909399'}

def format_post(post, user_id=None):
    """格式化帖子信息"""
    category_info = get_category_info(post.category)
    data = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'summary': post.summary or post.content[:200] + '...' if len(post.content) > 200 else post.content,
        'tags': post.tags.split(',') if post.tags else [],
        'category': category_info,
        'view_count': post.view_count,
        'like_count': post.like_count,
        'comment_count': post.comment_count,
        'is_essence': post.is_essence,
        'is_top': post.is_top,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'author': {
            'id': post.user.id,
            'username': post.user.username
        }
    }
    
    # 如果传入用户ID，检查是否已点赞和收藏
    if user_id:
        liked = Like.query.filter_by(user_id=user_id, post_id=post.id).first() is not None
        favorited = Favorite.query.filter_by(user_id=user_id, post_id=post.id).first() is not None
        data['is_liked'] = liked
        data['is_favorited'] = favorited
    
    return data

def format_comment(comment, user_id=None):
    """格式化评论信息"""
    data = {
        'id': comment.id,
        'content': comment.content,
        'like_count': comment.like_count,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'author': {
            'id': comment.user.id,
            'username': comment.user.username
        },
        'replies': []
    }
    
    # 递归格式化回复
    for reply in comment.replies:
        data['replies'].append(format_comment(reply, user_id))
    
    # 如果传入用户ID，检查是否已点赞
    if user_id:
        liked = Like.query.filter_by(user_id=user_id, comment_id=comment.id).first() is not None
        data['is_liked'] = liked
    
    return data

@community_bp.route('/community/posts', methods=['GET'])
def get_posts():
    """获取帖子列表"""
    # 处理空字符串安全转换为int
    page_str = request.args.get('page')
    per_page_str = request.args.get('per_page')
    category = request.args.get('category', '')
    tag = request.args.get('tag', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'latest')  # latest/hot/essence

    # 默认值
    page = 1
    if page_str and page_str != '':
        try:
            page = int(page_str)
        except (ValueError, TypeError):
            page = 1

    per_page = 10
    if per_page_str and per_page_str != '':
        try:
            per_page = int(per_page_str)
        except (ValueError, TypeError):
            per_page = 10
    
    query = Post.query
    
    # 筛选条件
    if category:
        query = query.filter_by(category=category)
    if tag:
        query = query.filter(Post.tags.like(f'%{tag}%'))
    if search:
        query = query.filter(Post.title.like(f'%{search}%') | Post.content.like(f'%{search}%'))
    if sort == 'essence':
        query = query.filter_by(is_essence=True)
    
    # 排序
    if sort == 'hot':
        # 热门排序：按点赞数+评论数+浏览数综合排序
        query = query.order_by(
            (Post.like_count + Post.comment_count + Post.view_count / 10).desc(),
            Post.created_at.desc()
        )
    elif sort == 'latest':
        # 最新排序：先置顶，再按创建时间
        query = query.order_by(Post.is_top.desc(), Post.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items
    
    # 获取当前用户ID（如果登录了）
    user_id = None
    try:
        user_id = get_jwt_identity()
    except:
        pass
    
    # 格式化返回
    return jsonify({
        'list': [format_post(post, user_id) for post in posts],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(pagination.total / per_page)
    }), 200

@community_bp.route('/community/posts/<int:post_id>', methods=['GET'])
def get_post_detail(post_id):
    """获取帖子详情"""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    
    # 增加浏览量
    post.view_count += 1
    db.session.commit()
    
    # 获取当前用户ID（如果登录了）
    user_id = None
    try:
        user_id = get_jwt_identity()
    except:
        pass
    
    return jsonify(format_post(post, user_id)), 200

@community_bp.route('/community/posts', methods=['POST'])
@jwt_required()
def create_post():
    """创建帖子"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['title', 'content', 'category']
    for field in required_fields:
        if field not in data or not data[field].strip():
            return jsonify({'error': f'{field}不能为空'}), 400
    
    # 验证分类
    valid_categories = [cat['value'] for cat in CATEGORIES]
    if data['category'] not in valid_categories:
        return jsonify({'error': '分类不正确'}), 400
    
    # 处理标签
    tags = data.get('tags', [])
    if isinstance(tags, list):
        tags_str = ','.join([t.strip() for t in tags if t.strip()])
    else:
        tags_str = ''
    
    post = Post(
        title=data['title'].strip(),
        content=data['content'].strip(),
        summary=data.get('summary', '').strip(),
        tags=tags_str,
        category=data['category'],
        user_id=user_id
    )
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify({
        'message': '帖子发布成功',
        'post_id': post.id,
        'post': format_post(post, user_id)
    }), 201

@community_bp.route('/community/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    """更新帖子"""
    user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    
    if post.user_id != user_id:
        return jsonify({'error': '无权限修改此帖子'}), 403
    
    data = request.get_json()
    
    if 'title' in data and data['title'].strip():
        post.title = data['title'].strip()
    if 'content' in data and data['content'].strip():
        post.content = data['content'].strip()
    if 'summary' in data:
        post.summary = data['summary'].strip()
    if 'category' in data:
        valid_categories = [cat['value'] for cat in CATEGORIES]
        if data['category'] in valid_categories:
            post.category = data['category']
    if 'tags' in data:
        if isinstance(data['tags'], list):
            post.tags = ','.join([t.strip() for t in data['tags'] if t.strip()])
    
    post.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': '帖子更新成功',
        'post': format_post(post, user_id)
    }), 200

@community_bp.route('/community/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    """删除帖子"""
    user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    
    if post.user_id != user_id:
        return jsonify({'error': '无权限删除此帖子'}), 403
    
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'message': '帖子删除成功'}), 200

@community_bp.route('/community/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    """点赞/取消点赞帖子"""
    user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    
    like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if like:
        # 取消点赞
        db.session.delete(like)
        post.like_count = max(0, post.like_count - 1)
        action = 'unliked'
    else:
        # 点赞
        like = Like(user_id=user_id, post_id=post_id)
        db.session.add(like)
        post.like_count += 1
        action = 'liked'
    
    db.session.commit()
    
    return jsonify({
        'message': f'{action == "liked" and "点赞" or "取消点赞"}成功',
        'action': action,
        'like_count': post.like_count
    }), 200

@community_bp.route('/community/posts/<int:post_id>/favorite', methods=['POST'])
@jwt_required()
def favorite_post(post_id):
    """收藏/取消收藏帖子"""
    user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    
    favorite = Favorite.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if favorite:
        # 取消收藏
        db.session.delete(favorite)
        action = 'unfavorited'
    else:
        # 收藏
        favorite = Favorite(user_id=user_id, post_id=post_id)
        db.session.add(favorite)
        action = 'favorited'
    
    db.session.commit()
    
    return jsonify({
        'message': f'{action == "favorited" and "收藏" or "取消收藏"}成功',
        'action': action
    }), 200

@community_bp.route('/community/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """获取帖子评论列表"""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    
    # 只获取一级评论（parent_id为None的）
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    
    # 获取当前用户ID（如果登录了）
    user_id = None
    try:
        user_id = get_jwt_identity()
    except:
        pass
    
    return jsonify([format_comment(comment, user_id) for comment in comments]), 200

@community_bp.route('/community/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    """发表评论"""
    user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    
    data = request.get_json()
    content = data.get('content', '').strip()
    parent_id = data.get('parent_id')
    
    if not content:
        return jsonify({'error': '评论内容不能为空'}), 400
    
    # 如果是回复评论，检查父评论是否存在
    if parent_id:
        parent_comment = Comment.query.get(parent_id)
        if not parent_comment or parent_comment.post_id != post_id:
            return jsonify({'error': '父评论不存在'}), 404
    
    comment = Comment(
        content=content,
        user_id=user_id,
        post_id=post_id,
        parent_id=parent_id
    )
    
    db.session.add(comment)
    post.comment_count += 1
    db.session.commit()
    
    return jsonify({
        'message': '评论发表成功',
        'comment': format_comment(comment, user_id)
    }), 201

@community_bp.route('/community/comments/<int:comment_id>/like', methods=['POST'])
@jwt_required()
def like_comment(comment_id):
    """点赞/取消点赞评论"""
    user_id = get_jwt_identity()
    comment = Comment.query.get(comment_id)
    
    if not comment:
        return jsonify({'error': '评论不存在'}), 404
    
    like = Like.query.filter_by(user_id=user_id, comment_id=comment_id).first()
    
    if like:
        # 取消点赞
        db.session.delete(like)
        comment.like_count = max(0, comment.like_count - 1)
        action = 'unliked'
    else:
        # 点赞
        like = Like(user_id=user_id, comment_id=comment_id)
        db.session.add(like)
        comment.like_count += 1
        action = 'liked'
    
    db.session.commit()
    
    return jsonify({
        'message': f'{action == "liked" and "点赞" or "取消点赞"}成功',
        'action': action,
        'like_count': comment.like_count
    }), 200

@community_bp.route('/community/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    return jsonify(CATEGORIES), 200

@community_bp.route('/community/user/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    """获取用户发布的帖子"""
    # 处理空字符串安全转换为int
    page_str = request.args.get('page')
    per_page_str = request.args.get('per_page')

    page = 1
    if page_str and page_str != '':
        try:
            page = int(page_str)
        except (ValueError, TypeError):
            page = 1

    per_page = 10
    if per_page_str and per_page_str != '':
        try:
            per_page = int(per_page_str)
        except (ValueError, TypeError):
            per_page = 10
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    query = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items
    
    # 获取当前用户ID（如果登录了）
    current_user_id = None
    try:
        current_user_id = get_jwt_identity()
    except:
        pass
    
    return jsonify({
        'list': [format_post(post, current_user_id) for post in posts],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    }), 200

@community_bp.route('/community/user/favorites', methods=['GET'])
@jwt_required()
def get_user_favorites():
    """获取用户收藏的帖子"""
    user_id = get_jwt_identity()
    # 处理空字符串安全转换为int
    page_str = request.args.get('page')
    per_page_str = request.args.get('per_page')

    page = 1
    if page_str and page_str != '':
        try:
            page = int(page_str)
        except (ValueError, TypeError):
            page = 1

    per_page = 10
    if per_page_str and per_page_str != '':
        try:
            per_page = int(per_page_str)
        except (ValueError, TypeError):
            per_page = 10
    
    # 查询用户收藏的帖子
    favorites = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.created_at.desc()).all()
    post_ids = [fav.post_id for fav in favorites]
    
    if not post_ids:
        return jsonify({
            'list': [],
            'total': 0,
            'page': page,
            'per_page': per_page
        }), 200
    
    # 按收藏时间排序
    query = Post.query.filter(Post.id.in_(post_ids))
    # 自定义排序，保持收藏的顺序
    posts = query.all()
    # 按照post_ids的顺序排序
    posts.sort(key=lambda x: post_ids.index(x.id))
    
    # 分页
    start = (page - 1) * per_page
    end = start + per_page
    paginated_posts = posts[start:end]
    
    return jsonify({
        'list': [format_post(post, user_id) for post in paginated_posts],
        'total': len(posts),
        'page': page,
        'per_page': per_page
    }), 200


@community_bp.route('/community/stats', methods=['GET'])
def get_community_stats():
    """获取社区统计数据"""
    logger.info("[COMMUNITY API] GET /community/stats")

    try:
        # 统计各种真实数据
        total_posts = Post.query.count()
        total_users = User.query.count()

        # 今日新帖 - 统计今天创建的帖子
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_posts = Post.query.filter(Post.created_at >= today_start).count()

        # 在线用户 - 简单统计所有非禁用用户就是在线用户
        # 如果需要精确在线，可以基于最后活跃时间实现，这里简化为总用户数
        online_users = total_users

        return jsonify({
            'total_posts': total_posts,
            'total_users': total_users,
            'today_posts': today_posts,
            'online_users': online_users
        }), 200

    except Exception as e:
        return jsonify({'error': f'获取统计数据失败: {str(e)}'}), 500
