# myshudan 书单视频制作生成工具  
## 软件功能  
这个工具能够把word文档或pdf文档生成视频，文档中的每一页等同于一个视频画面，每个画面的切换使用翻书特效，因此整个文档视频就像在读一本书一样。  
软件支持给视频添加BGM背景音乐，你也可以这个功能当成添加配音音频来使用。  

![界面截图](https://github.com/kjzysjk/myshudan/blob/main/case2.jpg)  

## 开发计划
- 开发使用图片素材
- 开发使用文本+图片模板制作书单页画面
- 开发对每个画面单独设置配音音频，或对每个画面使用配音文本生成配音

## 技术架构图
1) 从word或pdf提取图片
2) 把图片转成视频
3) 把视频拼接起来，每个视频的转场使用翻书特效
4) 对拉接的好的视频添加音频

## 环境部署
1) 安装 [ffmpeg-concat](https://github.com/transitive-bullshit/ffmpeg-concat)
2) 安装 ffmpeg、ffprobe 并添加到环境变量，也可以直接把 ffmpeg.exe 和 ffprobe.exe放到软件目录下<https://www.ffmpeg.org/>  
3) 安装python3.7+，根据代码中import安装相关依赖
4) python shudan.py 即可运行软件

## 直接使用整合包
我们已制作相应版本的软件windows整合包，下载解压缩后，运行 myshudan.exe 可直接打开软件使用。  
使用整合包，无需环境部署。  
整合包  <https://github.com/kjzysjk/myshudan/releases/download/v1.10/myshudan_v1.10.7z>  

**不论是代码开发还是直接使用整合包，电脑必须安装有office或wps。**  

### 配置介绍
由于作者水平有限，无法直接在整合包中解决ffmpeg-concat的打包，这是一个基于nodejs的东东，需要使用npm安装。  
因此整合包的ffmpeg-concat使用的是在线接口，
如果你本机成功安装ffmpeg-concat之后，请整合包文件夹下**ApiSetting.cfg**里的local_mode=0 修改为 local_mode=1 就能切换本机的ffmpeg-concat。  

## 心得
庞大的ffmpeg-concat仅仅是为了获取视频转场的翻书效果，但这个翻书特效是书单视频中最重要的一个效果。  
ffmpeg-concat是ffmpeg-gl-transition的另一个衍生物，
作者在寻遍全网也找不到已编译ffmpeg-gl-transition的ffmpeg.exe，自己也在尝试编译ffmpeg.exe中添加ffmpeg-gl-transition遭遇数次失败。  
作者在尝试使用cv opengl等方式来实现同样的效果，方便集成到软件中，减少软件复杂度。  

