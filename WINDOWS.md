# התקנה ב-Windows

> **הערה חשובה:** `setup.sh` עובד רק על מק. בווינדוס צריך להתקין ידנית,
> וזה שישה שלבים. הכלי עצמו (`transcribe.py`) עובד בווינדוס בלי שינוי —
> רק ההתקנה שונה.
>
> *לא הצלחנו לבדוק את ההוראות האלה על מכונת Windows אמיתית. אם משהו לא
> עובד, תגידו ואנחנו נתקן.*

---

## 1. מתקינים Miniforge

מורידים את המתקין מכאן:
https://github.com/conda-forge/miniforge/releases/latest

הקובץ נקרא `Miniforge3-Windows-x86_64.exe`. מתקינים רגיל, הכל ברירת מחדל.

בסוף ההתקנה יופיע בתפריט התחל פריט בשם **Miniforge Prompt**.
**את כל הפקודות הבאות מריצים שם**, לא ב-PowerShell או ב-CMD רגילים.

---

## 2. יוצרים סביבה

ב-Miniforge Prompt:

```
conda create -n transcribe python=3.11 -y
conda activate transcribe
```

---

## 3. מתקינים את מה שצריך

```
pip install faster-whisper
conda install -c conda-forge ffmpeg -y
```

`ffmpeg` הוא מה שמוציא את האודיו מקובץ וידאו. דרך conda זה עובד
בלי להתעסק עם PATH.

---

## 4. אומרים לכלי איפה לשמור

יוצרים תיקייה להערות, למשל `C:\Users\<השם שלך>\Desktop\Lectures`,
ואז:

```
echo C:\Users\<השם שלך>\Desktop\Lectures > %USERPROFILE%\.lecture-vault
```

שימו לב: `echo` בווינדוס מוסיף לפעמים רווח בסוף. אם זה עושה בעיות,
פשוט פתחו את הקובץ `.lecture-vault` בפנקס רשימות ותוודאו שיש בו
רק את הנתיב, בלי רווחים ובלי שורה ריקה.

---

## 5. יוצרים תיקייה לכל קורס

בתוך תיקיית ההערות, תיקייה לכל קורס. השם חופשי:

```
Lectures\
  71811 - Immunology\
  71204 - Basic Techniques\
```

ומעתיקים לתוך כל תיקייה את הקובץ המתאים מ-`course-packs\`,
בשם `_style.md`.

---

## 6. מריצים

ב-Miniforge Prompt, אחרי `conda activate transcribe`:

```
python C:\path\to\hebrew-lecture-pipeline\transcribe.py --latest --course 71811
```

זה ארוך. אפשר לקצר עם הקובץ `lecture.bat` שנמצא בתיקייה — מעתיקים אותו
למקום שנמצא ב-PATH, או פשוט מריצים אותו מתוך התיקייה של הפרויקט.

---

## הבדלים מול מק

| | מק | ווינדוס |
|---|---|---|
| התקנה | `bash setup.sh` | ידנית, השלבים למעלה |
| הרצה | `lecture --latest --course X` | `lecture.bat --latest --course X` |
| העתקה ללוח | `\| pbcopy` | `\| clip` |
| מיקום ההערות | `~/Desktop/Lectures` | `%USERPROFILE%\Desktop\Lectures` |

כל השאר זהה: אותו מודל, אותו דיוק, אותן רשימות מונחים.

---

## אם משהו נשבר

**"conda is not recognized"** — פתחתן CMD רגיל במקום Miniforge Prompt.

**התמלול יוצא ג'יבריש במקום עברית** — זה מצביע על בעיית קידוד.
הכלי כותב הכל ב-UTF-8 במפורש, אז זה כנראה העורך שבו פותחים את הקובץ.
נסו לפתוח ב-VS Code או ב-Notepad חדש (לא Notepad ישן).

**"ffmpeg not found"** — לוודא ש-`conda activate transcribe` רץ קודם.

**זה איטי מאוד** — על מחשב בלי GPU זה לוקח בערך פי 4 מזמן ההרצאה.
זה נורמלי. אם יש GPU של NVIDIA אפשר להאיץ משמעותית, כתבו ונוסיף הוראות.
