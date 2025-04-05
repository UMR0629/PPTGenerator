# PPTGenerator
## 代码文件目录
```
PPTGenerator
├── index   # PaperInfo等关键数据结构、前后端接口
│   └── index_module.py
├── pdf_scan    # PDF扫描模块
│   ├── config.yml  # 配置文件
│   ├── model_final.pth # 目标检测模型
│   ├── scan_pdf.py # PDF扫描主程序
│   └── test.pdf    # 测试用PDF
├── information_extractor   # 大模型交互模块
│   ├── extract_function.py
│   └── result_extraction.py
├── data_base   # 数据库模块
│   └── save_tree.py
├── generate_ppt    # PPT生成模块
│   └── generate_ppt.py
├── show.py  # 前端主程序
├── newpage.py  # 前端启动程序
├── data_clean  # 清洗后的原始数据
│   └── output
│── source  # ppt生成所使用的静态资源
├── detectron2-main.zip # 目标检测模型
├── paper_info.db # 数据库文件
├── requirements.txt    # 依赖包列表
├── Dockerfile  # build docker所用的配置文件
└── README.md   # 代码具体说明
```

## docker容器部署方法（docker desktop）
1. 在docker terminal中来到`/PPTGenerator`目录
2. 运行以下命令构建docker镜像
```bash
docker build -t pdf2ppt .
```
3. 使用以下命令启动：
```bash
docker run -it  --network host --name pdf-container pdf2ppt /bin/bash
```
4. 进入容器后，应当处于root@pdf-container:/app$，执行以下命令：
```bash
streamlit run newpage.py
```
即可启动服务。服务占用8501端口，可通过浏览器访问http://localhost:8501/ 进行访问。

## 部署过程中可能出现的问题（docker desktop）
1. build过程中，出现如下报错：
```
ERROR: failed to solve: python:3.10-slim
```
需要单独将python:3.10-slim镜像下载到本地，运行以下命令即可：
```bash
docker pull python:3.10-slim
```
2. build过程中，pytorch的安装失败
需要更换国内镜像源：在docker设置的docker engine中添加如下配置（下为本人的配置），并且选择右下角apply and start按钮：
```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://hub-mirror.c.163.com",
    "https://mirror.ccs.tencentyun.com",
    "https://mirrors.aliyun.com"
  ]
}
```
3. build过程中，matplotlib的安装慢/失败
可以单独进行下载：
```bash
pip install matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple
```
4. 启动streamlit后，浏览器无法访问8501端口
需要在docker desktop的设置中，选择resouce/network，勾选enable host networking即可

## docker容器以外的部署方法，详见部署文档
## 其他问题请联系作者
email：caoyifan0629@sjtu.edu.cn