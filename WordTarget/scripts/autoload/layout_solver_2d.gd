extends Node
class_name LayoutSolver2D

# 网格布局算法
static func layout_cards(boundary: Rect2, cards: Array, target_word: String, spacing: float = 6.0) -> Dictionary:
	# 1. 准备卡片信息，按面积降序（用于删词优先级）
	var items = []
	for card in cards:
		items.append({
			"word": card.word,
			"size": card.size,
			"area": card.size.x * card.size.y
		})
	items.sort_custom(func(a, b): return a.area > b.area)
	
	# 2. 找出所有单词中的最大宽度和最大高度（用于网格单元尺寸）
	var max_width = 0.0
	var max_height = 0.0
	for item in items:
		max_width = max(max_width, item.size.x)
		max_height = max(max_height, item.size.y)
	# 加上间距，作为网格步长
	var step_x = max_width + spacing
	var step_y = max_height + spacing
	
	# 3. 计算可用的网格行列数
	var grid_cols = max(1, int((boundary.size.x - max_width) / step_x) + 1)
	var grid_rows = max(1, int((boundary.size.y - max_height) / step_y) + 1)
	var total_cells = grid_cols * grid_rows
	
	
	# 4. 如果网格点不够放置所有单词，则删除多余的单词（优先删非目标的大单词）
	var target_index = -1
	for i in range(items.size()):
		if items[i].word == target_word:
			target_index = i
			break
	# 确保目标单词在列表中
	if target_index == -1:
		printerr("目标单词不在卡片列表中")
		return {}
	
	# 动态删减：如果单元格数少于卡片总数，移除多余的非目标单词（从大到小）
	var keep_items = items.duplicate()
	while keep_items.size() > total_cells:
		var removed = false
		# 优先删除非目标且面积最大的单词
		for i in range(keep_items.size()):
			if keep_items[i].word != target_word:
				keep_items.remove_at(i)
				removed = true
				break
		if not removed:
			# 若只剩下目标单词，则强行保留（不再删）
			break
	
	# 5. 生成所有网格中心点（可放置的位置）
	var grid_centers = []
	for row in range(grid_rows):
		for col in range(grid_cols):
			var center_x = boundary.position.x + col * step_x + max_width/2
			var center_y = boundary.position.y + row * step_y + max_height/2
			# 确保中心点在边界内（允许微调时超出边界，但后面会钳位）
			var center = Vector2(center_x, center_y)
			grid_centers.append(center)
	
	# 如果网格点数量仍少于保留的单词数，随机删除单词（保底）
	while keep_items.size() > grid_centers.size():
		for i in range(keep_items.size()):
			if keep_items[i].word != target_word:
				keep_items.remove_at(i)
				break
	
	# 打乱网格点顺序，实现随机分配
	grid_centers.shuffle()
	
	# 6. 分配位置并添加随机偏移（偏移范围为 ±最小卡片尺寸的 0.2 倍，且不超出边界）
	var result = {}
	for i in range(keep_items.size()):
		var item = keep_items[i]
		var center = grid_centers[i]
		# 随机偏移：偏移量不超过卡片半宽的 0.3 倍，且保证卡片不超出边界
		var offset_x = randf_range(-item.size.x * 0.15, item.size.x * 0.15)
		var offset_y = randf_range(-item.size.y * 0.15, item.size.y * 0.15)
		var final_center = center + Vector2(offset_x, offset_y)
		# 钳位，确保整个卡片在边界内
		var min_x = boundary.position.x + item.size.x/2
		var max_x = boundary.end.x - item.size.x/2
		var min_y = boundary.position.y + item.size.y/2
		var max_y = boundary.end.y - item.size.y/2
		final_center.x = clamp(final_center.x, min_x, max_x)
		final_center.y = clamp(final_center.y, min_y, max_y)
		result[item.word] = final_center
	
	# 7. 保底：确保至少含有目标单词和最少4张卡片（可能因边界过小导致不足）
	if result.size() < 4 or not result.has(target_word):
		result = _force_minimum(result, cards, boundary, target_word, spacing)
	
	return result

# 随机保底逻辑（与之前类似）
static func _force_minimum(current_map: Dictionary, all_cards: Array, boundary: Rect2, target_word: String, spacing: float) -> Dictionary:
	var new_map = current_map.duplicate()
	var need = 4 - new_map.size()
	var need_target = not new_map.has(target_word)
	
	var placed_rects = []
	for word in new_map.keys():
		for card in all_cards:
			if card.word == word:
				var center = new_map[word]
				placed_rects.append(Rect2(center - card.size/2, card.size))
				break
	
	var try_place = func(size: Vector2) -> Vector2:
		for _i in range(200):
			var cx = randf_range(boundary.position.x + size.x/2, boundary.end.x - size.x/2)
			var cy = randf_range(boundary.position.y + size.y/2, boundary.end.y - size.y/2)
			var center = Vector2(cx, cy)
			var rect = Rect2(center - size/2, size)
			var overlap = false
			for r in placed_rects:
				if r.grow(-spacing).intersects(rect):
					overlap = true
					break
			if not overlap:
				return center
		return Vector2.ZERO
	
	if need_target:
		for card in all_cards:
			if card.word == target_word:
				var pos = try_place.call(card.size)
				if pos == Vector2.ZERO:
					pos = boundary.position + boundary.size/2
				new_map[target_word] = pos
				placed_rects.append(Rect2(pos - card.size/2, card.size))
				need -= 1
				break
	
	var remaining = all_cards.duplicate()
	remaining.shuffle()
	remaining.sort_custom(func(a,b): return (a.size.x*a.size.y) > (b.size.x*b.size.y))
	for card in remaining:
		if need <= 0:
			break
		if new_map.has(card.word):
			continue
		var pos = try_place.call(card.size)
		if pos != Vector2.ZERO:
			new_map[card.word] = pos
			placed_rects.append(Rect2(pos - card.size/2, card.size))
			need -= 1
	
	return new_map
