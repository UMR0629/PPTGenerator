from generate_ppt import Generate_ppt

# 加载已有的PPT模板
ppt_path = "./1.百廿红-李一.pptx"
generate_ppt = Generate_ppt(ppt_path)
generate_ppt.add_cover("这是标题", "这是作者", "2021年5月")
menu_items = ["目录1", "目录2", "目录3", "目录4"]
generate_ppt.add_menu_4("./image22.jpg", menu_items)
menu_items = ["目录1","目录2", "目录3", "目录4", "目录5", "目录6"]
generate_ppt.add_menu_6("./image19.jpg", menu_items)
text = "这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。\n这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。这是一段文本。"
short_text = "这是短文本"
generate_ppt.add_all_text("ppt生成", text)
generate_ppt.add_text_image("ppt生成", text, "./image22.jpg")
generate_ppt.add_text_image("ppt生成", short_text, "./image19.jpg")
generate_ppt.save_ppt("output.pptx")