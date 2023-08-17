

async def upgrade_session(uc):
    """only useful if you have an undetected-Chromedriver session and you want to upgrade that
    session IN PLACE to a undetected-Nodriver session. It will close uc and takes the current url and
    user data path.

    :param uc: undetected-chromedriver driver object
    :return: undetected-nodriver "driver" object
    """
    import importlib
    try:
        import undetected_nodriver
    except ImportError:
        try:
            from pip._internal import main as pipmain
        except ImportError:
            try:
                from pip import main as pipmain
            except:
                raise Exception("could not find the system PIP to install undetected-nodriver.\n"
                                "please install it manually")
            pipmain(["install undetected-nodriver"])


    from undetected_nodriver import start, cdp

    user_data_dir = uc.user_data_dir or uc.options.user_data_dir
    current_url = uc.current_url
    dbg_h, dbg_p = uc.options.debugger_address.split(':')
    dbg_p = int(dbg_p)
    instance = await start(user_data_dir=user_data_dir, port=dbg_p, host=dbg_h)
    target_info = await instance.connection._send(cdp.target.get_targets())
    for page in instance.pages:
        if not page.target:
            for ti in target_info:
                if ti.target_id == page.target_id:
                    page.target = ti
    await instance.pages[-1].close()
    await instance.get(current_url)
    uc.service.stop()
    return instance