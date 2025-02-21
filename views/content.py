# @app.route('/content', methods=['POST'])
# @jwt_required()
# def add_content():
#     data = request.get_json()
#     title = data.get('title')
#     description = data.get('description')
#     category_id = data.get('category_id')
#     user_id = get_jwt_identity()

#     if not title or not description or not category_id:
#         return jsonify({"message": "Title, description, and category ID are required"}), 400

#     # Check if the category exists
#     category = Category.query.get(category_id)
#     if not category:
#         return jsonify({"message": "Category not found"}), 404

#     new_content = Content(
#         title=title,
#         description=description,
#         category_id=category_id,
#         status='pending',
#         user_id=user_id
#     )
#     db.session.add(new_content)
#     db.session.commit()
#     return jsonify({"message": "Content added successfully"}), 201