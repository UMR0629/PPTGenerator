storedata_dataclean.py：处理ppt识别后的数据，完成数据洗工作。
    1. 专注于处理title.txt和text.txt，将这些文本提出出来
    2.将text.txt中存在的标题提取出来，分割group（group可以视为一个标题）
    3.将group重新排序方便后续处理
    4.输入文件：output2；输出文件：output0
storedata_datacombine.py：处理output0，完成标题和文本的一一匹配
    1.将同一个标题下的普通text和特殊text区分（普通text就是正常文本，特殊text是图片、表格等）
    2.将所有普通text既所有正常文本合并为merged_text.txt，且复制其他文本包括title.txt;将结果保存到output3文件夹
    3.进行页间的文本合并，group_0为上一页在本页的剩余文本，故而合并两者，并将最终所有的group重新排序，结果保存在output4，这是最后要存到数据类里面的标题和对应文本内容。
    4.输入文件：output0；输出文件output3，output4

注意：
1. 需要按顺序调用storedata_dataclean.py和storedata_datacombine.py从而完成标题和对应文本的匹配。
