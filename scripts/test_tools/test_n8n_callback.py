import json
import requests

# 用户提供的完整 n8n 返回 JSON 数据
n8n_response = [
    {
        "output": {
            "desc_en": "Losing your beloved pet leaves an unfillable paw print on your heart. � Want to keep their memory cherished forever?\n\nIntroducing the Pet Fur Memory Charm Keychain – a beautiful way to keep your furry friend close! ✨\n\n*   **Forever Close:** Safely holds a precious snip of your pet's fur, always with you. �\n*   **Stylish & Sentimental:** Crafted from elegant leather with a loving paw-shaped design. 🌟\n*   **Heartfelt Comfort:** A unique keepsake offering solace and a tangible memory. 💖\n*   **Thoughtful Gift:** The perfect sympathy gift for any grieving pet parent. 🎁\n\nHonor their love and keep their spirit alive. Tap below to get yours! 👇\n\n#PetMemorial #DogLoss #CatLoss #GriefSupport #PetKeepsake",
            "desc_zh": "失去心愛的寵物，心中的爪印永遠無法填補。� 想讓他們的回憶永存心間嗎？\n\n隆重推出宠物毛发纪念钥匙扣——讓您的毛小孩永遠近在咫尺！✨\n\n*   **永不分離：** 安全收納您寵物珍貴的毛髮，時刻與您相伴。�\n*   **時尚感性：** 精心製作的優雅皮革，搭配充滿愛的爪形設計。�\n*   **溫馨慰藉：** 獨特紀念品，帶來心靈的慰藉與實質的回憶。💖\n*   **貼心禮物：** 送給任何正在經歷喪寵之痛的寵物父母的完美慰問禮。🎁\n\n紀念他們的愛，讓他們精神永存。點擊下方，立即擁有！👇\n\n#寵物紀念 #狗狗過世 #貓咪過世 #失去寵物 #寵物紀念品",
            "script_en": "\n[0-3s] Hook:\n  [Visual Scene] POV: Camera focused on an old, slightly faded photo of a beloved pet. A hand gently reaches in to touch the photo, looking sad.\n  [Audio/Voiceover] Soft, melancholic music. VO: \"Miss your furry friend?\"\n\n[3-12s] Solution/Demo:\n  [Visual Scene] Quick cut to a hand carefully opening a small, clear baggie of pet fur. Close-up shot of the paw-shaped leather keychain. Hand skillfully inserts the pet fur into the designated charm area. Cut to the finished keychain, now attached to a set of keys, glinting in the light. Person gently smiles, looking at the keychain.\n  [Audio/Voiceover] Upbeat, hopeful music starts. VO: \"Keep their love forever close. This beautiful leather keychain holds their precious fur!\"\n\n[12-15s] Hard CTA:\n  [Visual Scene] Person holding the keychain up, clearly visible, and points directly to the bottom left of the screen (where the yellow basket/shop link usually appears).\n  [Audio/Voiceover] Music crescendos. VO: \"Get yours now! Link below!\"\n",
            "script_zh": "\n[0-3秒] 钩子：\n  [视觉场景] POV：镜头聚焦在一张褪色、心爱的宠物旧照片上。一只手轻轻伸入触摸照片，表情悲伤。\n  [音频/旁白] 轻柔、忧郁的音乐。旁白: \"想念你的毛孩子吗？\"\n\n[3-12秒] 解决方案/演示：\n  [视觉场景] 快速切换到一只手小心翼翼地打开一小袋透明的宠物毛发。爪形皮质钥匙扣的特写镜头。手巧地将宠物毛发放入指定的坠饰区域。切换到制作完成的钥匙扣，现在挂在一串钥匙上，在灯光下闪闪发光。人物轻轻微笑，看着钥匙扣。\n  [音频/旁白] 欢快、充满希望的音乐响起。旁白: \"让他们的爱永远伴你左右。这款精美的皮质钥匙扣能珍藏他们珍贵的毛发！\"\n\n[12-15秒] 强力行动呼吁：\n  [视觉场景] 人物举起钥匙扣，清晰可见，并直接指向屏幕左下方（通常是黄色购物车/商店链接出现的位置）。\n  [音频/旁白] 音乐达到高潮。旁白: \"立即购买！点击下方链接！\"\n",
            "voice_en": "Missing your beloved pet?\nOur paw-shaped leather keychain is a beautiful way to keep their fur close, a lasting memory of your best friend.\nHonor their love. Get yours today!",
            "voice_zh": "想念你心爱的宠物吗？这款爪形皮质钥匙扣能帮你把它们的毛发珍藏，是纪念你最好朋友的美好方式。纪念它们的爱，今天就购买吧！",
            "img_p_en": "A pet memorial keychain on a polished wooden surface, next to a soft, cream-colored knitted blanket and a single, delicate white feather. Professional product photography, soft studio lighting, 8k resolution, hyper-realistic, bokeh, depth of field, cinematic composition, advertising masterpiece.",
            "img_p_zh": "一个宠物纪念钥匙扣，置于抛光的木质表面上，旁边是一条柔软的米色针织毯和一根纤细的白色羽毛。专业的商品摄影，柔和的影室灯光，8k分辨率，超现实主义，焦外虚化，景深，电影级构图，广告大片。"
        }
    }
]

# 构造请求数据
request_data = {
    "api_key": "tk_n8n_update_2025_safe",
    "product_id": "1731500998159798308",
    "model_name": "gpt-4",
    **n8n_response[0]
}

url = "http://localhost:8000/api/update_product/"
headers = {"Content-Type": "application/json"}

print("=" * 80)
print("发送测试请求到 update_product_api...")
print("=" * 80)
print(f"URL: {url}")
print(f"\n请求数据:")
print(json.dumps(request_data, indent=2, ensure_ascii=False))
print("=" * 80)

try:
    response = requests.post(url, json=request_data, headers=headers)
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code == 200:
        print("\n" + "=" * 80)
        print("✅ 请求成功！现在检查数据库中的存储情况...")
        print("=" * 80)
except Exception as e:
    print(f"\n❌ 请求失败: {str(e)}")
    import traceback
    traceback.print_exc()
