# 人猫搭档_Prompt模板

## 1. 万能入口句

```text
基于《人猫搭档 AIGC 统一出图规范 V1.0》，保持同一个女生、同一只白色银渐层猫、同一套真实拍立得生活摄影风格，只改变本次场景、动作、角度和服装，不改变核心视觉基因。
```

## 2. 通用 Prompt 结构

```text
【参考图锁定】
使用参考图锁定同一个年轻女生和同一只白色银渐层猫。
保持女生的长深色头发、大圆框眼镜、安静认真表情、清秀自然五官。
保持猫的白色银渐层毛色、圆脸、大圆眼、呆萌认真表情。

【场景】
{scene_description}

【动作关系】
{action_description}

【服装】
{clothing_description}

【镜头构图】
4:3，中景/半身，{angle}，真实生活摄影。

【画质风格】
接近拍立得画质，轻微颗粒噪点，自然光，低饱和奶油色调，真实衣服褶皱、猫毛、沙发/街道/楼道光影。

【禁止项】
不要换脸，不要换猫品种，不要卡通化，不要过度美颜，不要肢体错误，不要文字乱码。
```

## 3. 沙发绿植正面母版 Prompt

```text
根据参考图生成一张真实生活摄影风的人猫半身合照。

使用参考图锁定同一个年轻女生和同一只白色银渐层猫。
女生保持长深色头发、大圆框眼镜、清秀自然五官、安静略微认真的表情。
猫保持白色银渐层毛色、圆脸、大圆眼、呆萌认真表情、真实猫体型。

场景是温馨室内沙发，沙发和人物背后有大量绿色植物，整体像真实家居生活照。
女生和猫一起坐在沙发上，猫和人一样肚皮朝前坐着，女生轻轻搂着猫的肩膀。
人和猫都看向镜头，状态自然、日常、轻松。

人和猫都穿简约白色 T 恤。
女生的白色 T 恤胸口印着猫的脸，图案占胸口大面积，保留猫的头部和脖子。
猫的白色 T 恤胸口印着女生的脸，图案只保留女生头部，不要脖子。

4:3，中景半身构图，真实摄影质感，接近拍立得画质，轻微颗粒噪点，低饱和奶油色调。
衣服褶皱、沙发褶皱、植物光影都要自然真实。

禁止：不要换脸，不要换成其他猫，不要卡通风，不要过度美颜，不要塑料皮肤，不要多手多脚，不要文字乱码，不要衣服图案变形严重。
```

## 4. 送外卖正面 Prompt

```text
根据参考图生成同一个年轻女生和同一只白色银渐层猫的真实生活摄影图。

女生保持长深色头发、大圆框眼镜、安静认真的表情。
猫保持白色银渐层、圆脸、大眼睛、呆萌认真表情。

场景是城市街道，女生和猫作为送外卖搭档，停在一辆外卖电动车旁边。
女生坐在或站在电动车旁，猫坐在前车篮里，人和猫都看向镜头。
电动车后面有外卖箱，整体真实自然，不要夸张商业广告感。

女生穿白色 T 恤加简约外卖马甲，颜色以奶油白、浅咖、黑色边线为主。
猫穿迷你外卖马甲，和女生形成搭档感。
可以有简单爪印标志，但不要复杂乱码文字。

4:3，中景构图，真实街拍感，拍立得质感，轻微颗粒，自然光，街道背景轻微虚化。
衣服、外卖箱、电动车、猫毛都要真实。

禁止：不要换脸，不要换猫品种，不要让猫变成人形，不要多余手脚，不要文字乱码，不要过度锐化，不要塑料感。
```

## 5. Negative Prompt

```text
negative prompt:
different person, different face, different cat breed, cartoon, anime, painting, 3d render, plastic skin, over beautified face, exaggerated smile, distorted glasses, missing glasses, wrong hair, short hair, orange cat, ragdoll cat, long-haired cat, deformed cat body, humanized cat body, extra fingers, missing fingers, extra arms, extra legs, broken hands, twisted limbs, blurry face, low resolution, watermark, messy text, gibberish text, logo distortion, unnatural clothes print, bad anatomy, unrealistic lighting, overexposed, underexposed
```
