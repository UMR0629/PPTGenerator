from generate_ppt import Generate_ppt

# 加载已有的PPT模板
ppt_path = "../source/ppt_model/1.百廿红-李一.pptx"
generate_ppt = Generate_ppt(ppt_path)
generate_ppt.add_cover("这是标题", "这是作者", "2021年5月")
menu_items = ["目录1", "目录2", "目录3", "目录4"]
generate_ppt.add_menu("../source/img/image22.jpg", 3, menu_items)
# generate_ppt.add_menu_3("../source/img/image22.jpg", menu_items)
# menu_items = ["目录1", "目录2", "目录3", "目录4"]
# generate_ppt.add_menu_4("../source/img/image22.jpg", menu_items)
# menu_items = ["目录1","目录2", "目录3", "目录4", "目录5"]
# generate_ppt.add_menu_5("../source/img/image22.jpg", menu_items)
# menu_items = ["目录1","目录2", "目录3", "目录4", "目录5", "目录6"]
# generate_ppt.add_menu_6("../source/img/image19.jpg", menu_items)
text = "这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。\n这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。"
short_text = "这是短文本，很短的文本。"
mid_text = "这是中等长度的文本，不是很长，也不是很短。这是中等长度的文本，不是很长，也不是很短。"
# generate_ppt.add_all_text("ppt生成", text)
# generate_ppt.add_text_image("ppt生成", text, "../source/img/image22.jpg")
# generate_ppt.add_text_image("ppt生成", short_text, "../source/img/image19.jpg")
# generate_ppt.add_all_image("ppt生成",  "../source/img/image22.jpg")
# generate_ppt.add_all_image("ppt生成",  "../source/img/image19.jpg")
generate_ppt.add_text_double_image("ppt生成", mid_text, "../source/img/image22.jpg", "../source/img/image19.jpg")
generate_ppt.save_ppt("../source/ppt_model/output.pptx")