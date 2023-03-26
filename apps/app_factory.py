from config import conf


def app_factory(app_type):

    if app_type == 'lite':
        from apps.lite_app import LiteApp
        return LiteApp()

    elif app_type == 'victorinox':
        from apps.victorinox import Victorinox
        app = Victorinox()
        app.create(conf().get('app', {}).get('tools', []))
        return app

    elif app_type == 'wechat-roleplay':
        from apps.wechat_roleplay import WechatRolePlay
        app = WechatRolePlay()
        app.create(conf().get('app', {}).get('tools', []))
        return app

    else:
        raise NotImplementedError
