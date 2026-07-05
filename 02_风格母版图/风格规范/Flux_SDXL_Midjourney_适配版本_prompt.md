# Flux / SDXL / Midjourney 适配版本 Prompt

> 同一套《陈年烈狗》画风，在不同模型里的写法不一样。  
> Flux 更吃自然语言和细节描述；SDXL 更吃结构化标签和负面词；Midjourney 更吃画面关键词、构图和参数。

---

## 1. 通用角色信息

### 陶淮南

```text
Tao Huainan, blind Chinese young man, fair skin, clean and delicate features, soft black layered hair, large dark eyes without clear focus, gentle and sensitive temperament, clean youthful aura, light-colored outfit.
```

### 迟骋

```text
Chi Cheng, Chinese young man, tall and slim, healthy darker skin tone, short black hair, narrow single eyelids, sharp eyebrows, high nose bridge, defined jawline, cold and restrained temperament, dark outfit, quiet but protective presence.
```

### 童年版补充

```text
childhood version, around 8 years old, Tao Huainan wears a beige puffer jacket, knitted hat and scarf, holding a soft blanket; Chi Cheng is thin, guarded, wearing an old dark padded jacket, quiet and defensive.
```

### 成年版补充

```text
adult version, early twenties, Tao Huainan is calm and gentle, wearing a light jacket or plaid shirt; Chi Cheng is taller, colder, wearing a black turtleneck and dark coat, tech entrepreneur aura.
```

---

## 2. Flux 版本

Flux 推荐用完整自然语言，不要堆太多括号权重。

### 2.1 Flux 单人母版：陶淮南童年

```text
Create a high-quality semi-realistic Chinese manhua and Korean webtoon style character reference sheet. The character is Tao Huainan as an 8-year-old blind Chinese boy. He has fair milky skin, a soft round face, soft black short hair, and large dark eyes that look beautiful but unfocused, without a clear gaze direction. He looks timid, sensitive, quiet, and well cared for. He wears a beige puffer jacket, a light knitted hat, a thick scarf, and holds a soft pale blanket close to his chest. His hands have a subtle searching gesture. Clean neutral background, full-body or half-body character master image, soft warm light, low-saturation colors, delicate painterly rendering, consistent character design for a comic series. Do not make him look like a normal sighted child, do not make him adult-like, do not sexualize him.
```

### 2.2 Flux 单人母版：迟骋童年

```text
Create a high-quality semi-realistic Chinese manhua and Korean webtoon style character reference sheet. The character is Chi Cheng as an 8 to 9-year-old Chinese boy from a poor northern rural background. He is very thin, with visible bony structure, slightly darker yellow-brown skin, short black hair, narrow single eyelids, and a guarded downward gaze. His face is sharper than other children his age. He wears an old dark gray padded jacket and a black sweater, slightly oversized but clean. He stands quietly with a defensive posture, hands in pockets or hanging naturally, not looking directly at the viewer. He feels like a silent little stray dog who has just learned to survive. Clean background, low-saturation colors, delicate painterly rendering. Do not make him look like a refined rich young master, do not make him cute and round-faced.
```

### 2.3 Flux 双人场景：盲校牵手

```text
Create a cinematic comic panel in semi-realistic Korean webtoon and Chinese manhua style. Tao Huainan is an 8-year-old blind boy with milky fair skin, soft black hair, a round face, and large unfocused dark eyes. He wears a light beige winter jacket and holds a soft blanket. Chi Cheng is an 8 to 9-year-old thin boy with darker skin, short black hair, narrow single eyelids, and a quiet guarded expression, wearing an old dark padded jacket. They are in a blind school dormitory at night, sitting on two small metal beds facing each other. A scarf or towel is tied through the bed railings, and both children hold the ends to feel connected. Warm dim dormitory light, quiet atmosphere, protective childhood companionship, no romantic or adult tone. Cinematic framing, detailed fabric folds, low-saturation colors, emotional storytelling.
```

### 2.4 Flux 成年重逢图

```text
Create a cinematic semi-realistic Chinese manhua / Korean webtoon illustration. Adult Tao Huainan, early twenties, blind, fair skin, soft black layered hair, large unfocused dark eyes, gentle and calm temperament, wearing a light jacket. Adult Chi Cheng, mid-twenties, tall and slim, short black hair, narrow single eyelids, sharp face, cold and restrained expression, wearing a black coat. They stand close in a dim hotel corridor during a heavy rain night at a remote medical aid site. Tao Huainan slightly raises his face toward Chi Cheng but his eyes do not focus. Chi Cheng looks down at him with suppressed emotion. Warm corridor light contrasts with cold blue rain outside. The mood is reunion, restraint, pain, and unresolved affection. Keep both characters consistent across the series.
```

---

## 3. SDXL 版本

SDXL 推荐“标签 + 结构化描述 + 负向提示词”。

### 3.1 SDXL 通用正向风格

```text
(masterpiece, best quality, high resolution, ultra-detailed), Korean webtoon style, high-end Chinese manhua illustration, semi-realistic digital painting, painterly rendering, cinematic storyboard composition, delicate emotional expression, realistic fabric folds, soft skin shading, low-saturation color palette, warm-cool lighting contrast, movie still feeling, clean composition, consistent character design
```

### 3.2 SDXL 通用负向

```text
low quality, worst quality, blurry, bad anatomy, bad hands, extra fingers, missing fingers, deformed face, inconsistent face, different hairstyle, different skin tone, wrong age, duplicate character, child sexualization, adult-like child, overly cute chibi, flat anime style, messy background, text, watermark, logo, overexposed, bad perspective, distorted body, nsfw
```

### 3.3 SDXL 陶淮南童年母版

```text
(masterpiece, best quality, ultra-detailed), Korean webtoon style, Chinese manhua illustration, semi-realistic painterly rendering, character reference sheet, clean background,
Tao Huainan, 8-year-old blind Chinese boy, milky fair skin, soft round face, soft black short hair, large dark eyes without clear focus, unfocused gaze, timid and sensitive expression, beige puffer jacket, light knitted hat, thick scarf, holding a pale soft blanket, subtle searching hand gesture, warm soft lighting, low saturation, delicate fabric folds, consistent character design
```

Negative:

```text
normal focused eyes, adult-like child, sexualized child, chibi, overly cute, different hairstyle, blonde hair, bright colorful clothes, bad hands, bad eyes, watermark, text
```

### 3.4 SDXL 迟骋童年母版

```text
(masterpiece, best quality, ultra-detailed), Korean webtoon style, Chinese manhua illustration, semi-realistic painterly rendering, character reference sheet, clean background,
Chi Cheng, 8-year-old Chinese boy from poor northern rural background, very thin body, bony frame, darker yellow-brown skin, short black hair, narrow single eyelids, downward guarded gaze, quiet defensive expression, old dark gray padded jacket, black sweater, slightly oversized clothes, hands in pockets, standing near a wall, silent stray dog feeling, low-saturation colors, soft dramatic lighting, consistent character design
```

Negative:

```text
fair milky skin, cute round face, rich young master, smiling brightly, colorful clothing, adult-like child, sexualized child, chibi, bad anatomy, bad hands, watermark, text
```

### 3.5 SDXL 成年双人重逢

```text
(masterpiece, best quality, ultra-detailed), Korean webtoon style, Chinese manhua illustration, semi-realistic digital painting, cinematic comic panel, emotional tension, warm-cool contrast,
adult Tao Huainan, early twenties, blind Chinese young man, fair skin, soft black layered hair, large unfocused dark eyes, gentle calm expression, light jacket, clean youthful aura,
adult Chi Cheng, mid twenties, tall slim Chinese young man, healthy darker skin tone, short black hair, narrow single eyelids, sharp eyebrows, high nose bridge, defined jawline, cold restrained expression, black coat,
they stand close in a dim hotel corridor during heavy rain, Tao Huainan slightly raises his face but eyes remain unfocused, Chi Cheng looks down with suppressed emotion, warm corridor light, cold blue rain outside, cinematic framing, restrained reunion, painful silence, consistent character identity
```

Negative:

```text
different characters, inconsistent faces, focused eyes for Tao Huainan, wrong age, old face, female face, overly romantic cliché, nsfw, bad hands, extra fingers, watermark, text, messy background
```

---

## 4. Midjourney 版本

MJ 推荐简洁、视觉导向、参数清晰。

### 4.1 MJ 陶淮南童年母版

```text
Tao Huainan as an 8-year-old blind Chinese boy, milky fair skin, soft round face, soft black short hair, large dark eyes without clear focus, timid and sensitive expression, beige puffer jacket, light knitted hat, thick scarf, holding a pale soft blanket, clean character reference sheet, semi-realistic Korean webtoon style, high-end Chinese manhua illustration, painterly rendering, soft warm light, low saturation, delicate fabric folds --ar 2:3 --stylize 150 --v 6
```

### 4.2 MJ 迟骋童年母版

```text
Chi Cheng as an 8-year-old Chinese boy from poor northern rural background, very thin bony body, darker yellow-brown skin, short black hair, narrow single eyelids, guarded downward gaze, quiet defensive expression, old dark gray padded jacket, black sweater, hands in pockets, standing near a wall, silent stray dog feeling, clean character reference sheet, semi-realistic Korean webtoon style, high-end Chinese manhua illustration, painterly rendering, low saturation --ar 2:3 --stylize 150 --v 6
```

### 4.3 MJ 成年双人重逢

```text
adult Tao Huainan, blind Chinese young man with fair skin, soft black layered hair, large unfocused dark eyes, gentle calm aura, light jacket, and adult Chi Cheng, tall slim Chinese young man with short black hair, narrow single eyelids, sharp face, cold restrained expression, black coat, standing very close in a dim hotel corridor during heavy rain, warm corridor light and cold blue rain outside, restrained reunion, painful silence, cinematic comic panel, semi-realistic Korean webtoon style, high-end Chinese manhua illustration, painterly rendering, emotional tension, movie still --ar 16:9 --stylize 200 --v 6
```

### 4.4 MJ 清吧结局图

```text
blind Chinese young man with fair skin and soft black hair sitting on a small bar stage, playing acoustic guitar under warm yellow spotlight, his large dark eyes unfocused, gentle and calm expression, another tall young man with black short hair and dark coat sitting quietly at a small table watching him, golden retriever lying near the stage as symbolic memory, warm intimate music bar, cinematic lighting, semi-realistic Korean webtoon style, high-end Chinese manhua illustration, painterly rendering, emotional finale, movie still --ar 16:9 --stylize 250 --v 6
```

### 4.5 MJ 一致性技巧

```text
same character design, consistent face, consistent hairstyle, recurring outfit, visual continuity, same comic series
```

建议参数：

```text
--seed 12345
--stylize 100 到 250
--ar 2:3    # 人物母版
--ar 16:9   # 场景分镜
--ar 9:16   # 竖屏连载
```

---

## 5. GPT Image 版本

GPT Image 更适合自然语言指令，直接说清楚“要生成什么”。

### 5.1 GPT Image 人物母版通用指令

```text
请生成一张《陈年烈狗》角色母版图，风格为韩漫 / 国漫半写实厚涂，电影感人物设定图，干净背景，高完成度。重点是稳定人物五官、发型、肤色、身材比例、服装和气质，方便后续系列图片保持一致。
```

### 5.2 GPT Image 陶淮南童年

```text
请生成陶淮南童年版人物母版图。陶淮南是8岁左右的中国男孩，失明，皮肤奶白，软乎乎小圆脸，黑色柔软短发，眼睛很大很黑亮但没有明确聚焦，视线有空感。表情胆怯、敏感、乖巧。穿米白色厚羽绒服，戴浅色毛线帽和围巾，怀里抱着浅色小毯子，手部有轻微摸索感。画面为半身到全身之间，干净背景，低饱和，柔和暖光，韩漫 / 国漫半写实厚涂风格。不要让他的眼神看起来像正常聚焦，不要成人化，不要暧昧化儿童角色。
```

### 5.3 GPT Image 迟骋童年

```text
请生成迟骋童年版人物母版图。迟骋8到9岁，来自北方农村，身形很瘦，骨架明显，肤色偏黑黄，黑色短发，薄单眼皮，眼神向下，表情沉默、防备、冷淡。穿深灰色旧棉服和黑色毛衣，衣服略不合身但干净，双手插兜或自然垂着，站姿贴墙，不主动看镜头。整体像一只警觉的小野狗。风格为韩漫 / 国漫半写实厚涂，干净背景，低饱和，高完成度角色设定图。不要画成精致少爷，不要画得太白，不要成人化。
```

### 5.4 GPT Image 成年双人重逢

```text
请生成一张《陈年烈狗》成年重逢阶段的双人漫画分镜图。风格为韩漫 / 国漫半写实厚涂，电影感构图，低饱和，冷暖对比光影。

陶淮南22到25岁，失明，皮肤白净，黑色柔软碎发，眼睛明亮但没有明确聚焦，气质温和清透，穿浅色外套。迟骋23到25岁，高大修长，肤色比陶淮南更深，黑色短发，薄单眼皮，眉眼锋利，穿深色外套，表情冷淡克制。

场景是云南医援点的雨夜宾馆走廊。窗外是深蓝色暴雨，走廊里只有暖黄色小灯。两人近距离面对面站着，陶淮南微微仰头但眼神不聚焦，迟骋低头看他，表情压着情绪。画面表达多年分离后的重逢、疏离、疼痛和克制。保持两位角色的五官、发型、年龄和服装风格一致。
```

---

## 6. 平台选择建议

| 平台 | 适合做什么 | 优点 | 注意点 |
|---|---|---|---|
| Flux | 人物母版、自然语言细节、电影感场景 | 理解中文/自然语言强，质感好 | 负面词作用不如 SDXL 稳，要把禁止项写进正向描述 |
| SDXL | 批量生产、LoRA、IP-Adapter、角色锁定 | 可控性强，适合工作流 | 需要参考图和 ControlNet / IP-Adapter 提升一致性 |
| Midjourney | 封面、氛围图、电影感大场景 | 审美强，出图漂亮 | 角色一致性弱，需要 seed + reference |
| GPT Image | 复杂语义、中文指令、场景理解 | 很适合按故事生成 | 批量一致性仍需母版图辅助 |

---

## 7. 推荐工作流

```text
1. 用 GPT Image 或 Flux 生成角色母版
2. 筛选最稳定版本，放入 references/character_master/
3. SDXL + IP-Adapter / LoRA 做批量章节图
4. Midjourney 做封面和高氛围海报
5. 每章先生成 9宫格脚本，再逐格生成
6. 所有图片统一记录 prompt、seed、参考图路径、版本号
```

---

## 8. 文件命名建议

```text
prompt_flux_tao_huainan_child_master_v01.md
prompt_sdxl_chi_cheng_child_master_v01.md
prompt_mj_adult_reunion_rain_corridor_v01.md
prompt_gptimage_blind_school_dormitory_v01.md
```
