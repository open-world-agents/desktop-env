def key_to_vk(key):
    vk = getattr(key, "vk", None)
    if vk is None:
        vk = getattr(key, "value", None).vk
    return vk
