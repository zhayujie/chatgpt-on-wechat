# timetask
一款支持自定义定时任务的chatgpt-on-wechat插件，支持自定义时间、轮询周期、自定义时间，包含动态添加任务、取消任务、查看任务列表等功能，一款定时任务系统的插件。


## **【插件功能介绍】**
##### 🎉功能一：
支持用户设定时间，添加定时任务，定时自动发消息；
* 时间支持自定义
* 日期支持轮询，支持每天、每周、工作日、具体日期、cron表达式等

##### 🎉功能二：
支持 普通的提醒消息、及链接其他插件的拓展功能。比如早报、点歌、搜索、转发GPT等，理论上已安装的插件均可一键调度

##### 🎉功能三：
支持动态的取消定时任务、随时查看任务列表等

##### 🎉功能四：
无侵入性，原项目无需改造，安装插件即可使用



## **【插件安装方法】**
1. clone本仓库 或 下载源代码（源码下载方式时，timetask文件夹会自动带上分支名，将文件夹名称去除，命名timetask为即可）
2. 将本插件的文件夹timetask, 放进 chatgpt-on-wechat 的 plugins 文件夹中（chatgpt-on-wechat启动后，会自动加载本插件）
3. 安装插件依赖库：进入 timetask 文件夹，执行命令：pip3 install -r requirements.txt
4. 至此，插件安转完毕，启动chatgpt-on-wechat，使用 timetask 插件



## **【如何使用 - 定时任务】**

Tips：与机器人对话，发送如下定时任务指令即可

### **一、添加定时任务**

【指令格式】：**$time 周期 时间 事件**
1. **$time**：指令前缀，当聊天内容以$time开头时，则会被当做为定时指令
2. **周期**：今天、明天、后天、每天、工作日、每周X（如：每周三）、YYYY-MM-DD的日期、cron表达式
3. **时间**：X点X分（如：十点十分）、HH:mm:ss的时间
4. **事件**：想要做的事情 （支持普通提醒、以及项目中的拓展插件，详情如下）
5. **群标题（可选）**：可选项，不传时，正常任务； 传该项时，可以支持私聊给目标群标题的群，定任务（格式为：group[群标题]，注意机器人必须在目标群中）

【备注】：目前第5点的支持的通道：itchat（即微信)、ntchat（windows版微信)、ntwork(windows版企业微信)
```
事件-拓展功能：默认已支持早报、搜索、点歌

示例 - 早报：$time 每天 10:30 早报
示例 - 点歌：$time 明天 10:30 点歌 演员
示例 - 搜索：$time 每周三 10:30 搜索 乌克兰局势
示例 - 提醒：$time 每周三 10:30 提醒我健身
示例 - cron：$time cron[0 * * * *] 准点报时
示例 - GPT：$time 每周三 10:30 GPT 夸一夸我
示例 - 画画：$time 每周三 10:30 GPT 画一只小老虎
示例 - 群任务：$time 每周三 10:30 滴滴滴 group[群标题]

拓展功能效果：将在对应时间点，自动执行拓展插件功能，发送早报、点歌、搜索等功能。
文案提醒效果：将在对应时间点，自动提醒（如：提醒我健身）

Tips：拓展功能需要项目已安装该插件，更多自定义插件支持可在
 timetask/config.json 的 extension_function 自助配置即可。
```
![添加定时任务](https://github.com/haikerapples/timetask/blob/master/images/addTask_all.jpg)
	
	
### **二、取消定时任务**

##### **方法一、直接通过任务编号，取消定时任务**

【指令格式】：**$time 取消任务 任务编号**
1. **$time 取消任务**：指令前缀，以此前缀，会取消定时任务
2. **任务编号**：机器人回复的任务编号（添加任务成功时，机器人回复中有）

![取消定时任务](https://github.com/haikerapples/timetask/blob/master/images/cancelTask.jpg)

	

##### **方法二、先查询任务编号列表，然后选择要取消的任务编号，取消定时任务**

1. 【指令格式】：$time 任务列表
![任务列表](https://github.com/haikerapples/timetask/blob/master/images/timeTasks.jpg)


2. 根据任务列表，选择要取消的任务编号，执行上面的方法一（直接通过任务编号，取消定时任务）
![取消任务](https://github.com/haikerapples/timetask/blob/master/images/cancelTask.jpg)

### **三、查看定时任务列表**

【指令格式】：**$time 任务列表**
*  指令执行成后，机器人会将所有 **待执行的任务列表**，回复出来
*  已过期或已被消费过的任务会自动过滤

![任务列表](https://github.com/haikerapples/timetask/blob/master/images/timeTasks.jpg)


### **四、插件文件介绍**

##### 配置文件：config.json

```
{
  #定时任务前缀（以该前缀时，会被定时任务插件捕获）
  "command_prefix": "$time", 
  
  #是否开启debug（会输出日志）
  "debug": false,  
  
  #检测频率（默认1秒一次，注意不建议修改！！如果任务带秒钟，则可能会被跳过）
  "time_check_rate": 1, 
  
  #Excel中迁移任务的时间（默认在凌晨4点将Excel 任务列表sheet 中失效的任务 迁移至 -> 历史任务sheet中）
  "move_historyTask_time": "04:00:00", 

  #是否每个任务回复前，均 路由查询一遍是否能被其他插件解释，若会被解释，则使用解释内容回复；否则继续查询是否开启了拓展功能，如果均不可被消费，则最终使用原始内容兜底
  #比如 $time 今天 13:35 搜索股票，到达目标时间，则会将 “搜索股票”的关键词默认路由到其他插件查询一遍，如果可以被其他插件解释，则再会使用使用解释后的内容回复。
  #定时内容可自由设定，比如 “搜索股票”、“$tool 查询天气”，只要你的工程的插件可以解释关键字即可（前面2个内容为示例，是否可以成功取决于你工程是否有识别该关键字的插件）
  "is_open_route_everyReply": true,
  
  #是否开启拓展功能（开启后，会识别项目中已安装的插件，如果命中 extension_function中的前缀，则会将消息路由转发给目标插件）
  "is_open_extension_function": true,
  
  #支持的拓展功能列表（理论上 已安装的插件，均支持路由转发，其他插件可自主配置，参考早报的配置方式）
  "extension_function":
  [
    {
      # 触发词
      "key_word": "早报",
      
      # 路由插件的 指令前缀
      "func_command_prefix":"$tool "
    },
    {
      "key_word": "点歌",
      "func_command_prefix": "$"
    },
    {
      "key_word": "搜索",
      "func_command_prefix": "$tool google "
    },
    {
      # 触发词
      "key_word": "GPT",
      "func_command_prefix": "GPT"
    }
  ]
}
```
![配置文件](https://github.com/haikerapples/timetask/blob/master/images/confige_reply.jpg)



### **五、其他**
##### 查看所有定时任务指令：
![所有指令](https://github.com/haikerapples/timetask/blob/master/images/allTaskCode.jpg)

##### 任务Excel文件：timetask/timeTask.xlsx
```
定时任务 - sheet： 存放当天要消费的任务

历史任务 - sheet： 存放历史已消费的任务
```