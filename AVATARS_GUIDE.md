

# 🎨 Avatar Guide

## 📁 The `avatars` Folder Structure

Your avatars must be placed in the `avatars/` folder right next to your `yrok2_gui.py` file.

```text
PythonProject/
├── yrok2_gui.py
├── avatars/
│   ├── avatar_neutral.png
│   ├── avatar_happy.png
│   ├── avatar_furious.png
│   ├── avatar_sad.png
│   ├── avatar_angry.png

```

## 🖼️ File Names

Each emotion has its own specific file name:

| Emotion | File Name | When it is used |
| --- | --- | --- |
| Neutral | `avatar_neutral.png` | Default/Normal state |
| Happy | `avatar_happy.png` | Gratitude, greetings |
| Confused | `avatar_confused.png` | Surprise, not understanding |
| Sad | `avatar_sad.png` | Errors, issues |
| Angry | `avatar_angry.png` | Annoyance, irritation |

## 📐 Size Recommendations

### Optimal dimensions:

* **Width:** 200-400px
* **Height:** Any (scales automatically)
* **Format:** PNG with transparency
* **Aspect Ratio:** Any (vertical or square works best)

### Examples:

* ✅ 200x200 (square)
* ✅ 250x450 (vertical)
* ✅ 300x300 (square)
* ✅ 200x350 (vertical)

## 🎨 How the System Works

### 1. Loading

```python
# The program looks for the specific file
avatar_path = f"avatars/avatar_{emotion}.png"

# If not found, it falls back to neutral
if not exists: use avatar_neutral.png

# If neutral is also missing, it shows an emoji
if not exists: show emoji fallback

```

### 2. Scaling

```python
# Automatic scaling
max_width = 200px
height = auto (proportional)

# LANCZOS filter is used for high quality
Image.Resampling.LANCZOS

```

### 3. Animation

```python
# When the emotion changes:
1. Scales up to 220px (10% increase)
2. Delay of 100ms
3. Returns to 200px

```

## 🔄 Fallback System

### Level 1: Attempt to load the emotion

```text
avatars/avatar_happy.png

```

### Level 2: If not found, use neutral

```text
avatars/avatar_neutral.png

```

### Level 3: If neutral is missing, use emoji

```text
😊 (text emoji)

```

## 💡 Tips

### For the best look:

1. **Use transparent PNGs** - the background underneath will be your dark GUI theme.
2. **Center the image** - it will be centered inside the circular avatar panel.
3. **Consistent style** - keep all avatars in the same art style.
4. **Clear emotions** - use easily recognizable facial expressions.

### Style Examples:

* 🎨 Cartoon characters
* 🤖 Robots with different expressions
* 😊 Stylized emojis
* 👤 Silhouettes with emotion icons
* 🎭 Masks with expressions

## 🛠️ Creating Avatars

### Option 1: Use ready-made emojis

1. Find high-resolution emojis (512x512 or larger).
2. Save them as PNG files.
3. Name them according to the emotion list.

### Option 2: Create your own

1. Use an image editor (Photoshop, GIMP, Figma).
2. Create 10 variants with different emotions.
3. Export them as PNGs with a transparent background.
4. Name the files correctly.

### Option 3: AI Generation

1. Use DALL-E, Midjourney, or Stable Diffusion.
2. Prompt: *"robot avatar showing [emotion], simple, clean, transparent background"*.
3. Generate the variants.
4. Save and rename them.

## 📝 Example AI Prompts

```text
Neutral: "friendly robot avatar, neutral expression, simple design, transparent background"
Happy: "friendly robot avatar, happy smiling, simple design, transparent background"
Thinking: "friendly robot avatar, thinking pose, hand on chin, transparent background"
Excited: "friendly robot avatar, excited expression, stars in eyes, transparent background"
Confused: "friendly robot avatar, confused expression, question mark, transparent background"
Sad: "friendly robot avatar, sad expression, tear, transparent background"
Angry: "friendly robot avatar, angry expression, red face, transparent background"
Surprised: "friendly robot avatar, surprised expression, wide eyes, transparent background"
Cool: "friendly robot avatar, cool expression, sunglasses, transparent background"
Love: "friendly robot avatar, love expression, hearts, transparent background"

```

## 🔍 Testing & Troubleshooting

### Is it set up correctly?

1. Run `python yrok2_gui.py`.
2. Look at the avatar at the top.
3. Type "Thank you" - it should change to *happy*.
4. Type "Error" - it should change to *sad*.

### If it's not working:

1. Check the file names (must be lowercase!).
2. Check the file extension (`.png`).
3. Check the folder path (the `avatars` folder must be right next to `yrok2_gui.py`).
4. Check file access permissions.

## 📊 Technical Details

### Supported formats:

* ✅ PNG (recommended)
* ✅ JPG/JPEG
* ✅ GIF (first frame only)
* ❌ SVG (not supported)

### Processing under the hood:

```python
# Loading
img = Image.open(avatar_path)

# Scaling
max_width = 200
ratio = max_width / img.width
new_height = int(img.height * ratio)
img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

# Conversion for GUI
photo = ImageTk.PhotoImage(img, master=root)

```

## 🎯 Quick Start

### If you already have avatars:

1. Create an `avatars` folder next to your `yrok2_gui.py` file.
2. Place your PNG files inside it.
3. Rename them according to the table above.
4. Run the program.

### If you don't have avatars yet:

1. The program will simply use standard text emojis.
2. Everything will work perfectly just like before.
3. You can add the real avatars later whenever they are ready.

---

**Now your assistant can use real images! 🎨✨**
