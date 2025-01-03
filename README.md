# AI Interactive Novel

一个由AI驱动的互动小说平台，读者可以通过投票决定故事的发展方向。

## Heroku部署步骤

1. 安装Heroku CLI并登录:
```bash
heroku login
```

2. 创建Heroku应用:
```bash
heroku create your-app-name
```

3. 添加PostgreSQL数据库:
```bash
heroku addons:create heroku-postgresql:mini
```

4. 设置环境变量:
```bash
heroku config:set OPENAI_API_KEY=your_openai_api_key
```

5. 部署代码:
```bash
git push heroku main
```

6. 启动worker进程:
```bash
heroku ps:scale worker=1
```

## 远程管理命令

1. 清理数据库:
```bash
heroku run python manage.py clean
```

2. 启动机器人:
```bash
heroku run python manage.py start
```

3. 停止机器人:
```bash
heroku ps:stop worker.1
```

## 本地开发

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 设置环境变量:
```bash
cp .env.example .env
# 编辑.env文件，填入必要的配置
```

3. 运行网站:
```bash
cd web && uvicorn app.main:app --reload
```

4. 运行机器人:
```bash
python manage.py start
``` 