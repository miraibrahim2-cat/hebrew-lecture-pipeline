# תמלול הרצאות בעברית — מקומי, חינם, בלי להעלות כלום לרשת

*Local Hebrew lecture transcription. Nothing is uploaded anywhere.*

---

## הבעיה

NotebookLM ודומיו מתמללים הרצאות בעברית בצורה בינונית, ובעיקר נכשלים בדיוק במקום
הכי חשוב: **מונחים מקצועיים באנגלית שנאמרים בתוך משפט בעברית**. באותה הרצאה אחת,
`ריזוביום` יכול להופיע כ-`ריזוגיה`, `ריסוקיום` ו-`אריזוביום`. אחרי סמסטר שלם,
אי אפשר לחפש כלום בסיכומים.

דוגמה אמיתית מהרצאת מיקרוביולוגיה בת 28 דקות:

| NotebookLM | הכלי הזה |
|---|---|
| `obמניום אוקסידיזing בקטריה` | `אמוניום אוקסידייזינג בקטריה` |
| `OA אמני אקסידיזing ארקיה` | `אמוניום אוקסידייזינג ארקיע` |
| `d הזוטרופים D זה ש אזו זה חנקן` | `דיאזוטרופים` |

ובנוסף: אין צורך להעלות את ההקלטה לשום שרת, אין תור, ואפשר לרוץ על עשר הרצאות
ברצף בלילה.

## מה זה עושה

לוקח קובץ הרצאה (וידאו או אודיו), ומייצר:

- **תמלול** בעברית, בקובץ טקסט
- **קובץ כתוביות** עם חותמות זמן, כדי לקפוץ לרגע מסוים בהקלטה

הכול רץ על המחשב שלך. המודל הוא
[ivrit-ai/whisper-large-v3-turbo](https://huggingface.co/ivrit-ai), שעבר אימון
ייעודי לעברית ומטפל גם באנגלית ובערבוב של השתיים.

**מהירות:** בערך פי 4 מזמן אמת על MacBook עם שבב M. הרצאה של 45 דקות לוקחת
כ-10 דקות ברקע.

---

## התקנה

```bash
bash setup.sh
```

מתקין את מה שחסר (ffmpeg, סביבת Python, המודל), שואל איפה לשמור את ההערות,
ומתקין פקודה בשם `lecture`. אפשר להריץ שוב בלי נזק — הוא מדלג על מה שכבר קיים.

צריך macOS עם [Homebrew](https://brew.sh). ההורדה הראשונה של המודל היא כ-1.5 ג'יגה,
פעם אחת.

---

## שימוש

```bash
# הקובץ האחרון שהורדת
lecture --latest --course 71811

# קובץ מסוים
lecture ~/Downloads/lecture3.mp4 --course 71811

# כמה קבצים ביחד (המודל נטען פעם אחת)
lecture ~/Downloads/*.m4a --course 71811

# להעביר את הקובץ המקורי מ-Downloads אחרי התמלול
lecture --latest --course 71811 --archive

# אילו קורסים מוגדרים
lecture --list
```

התמלול נכתב לתוך `<תיקיית ההערות>/<קורס>/transcripts/`.

**איך יוצרים קורס:** פשוט תיקייה חדשה בתיקיית ההערות. השם חופשי, ו-`--course`
מזהה לפי מספר הקורס או לפי חלק מהשם.

---

## אוצר מילים לכל קורס

הדיוק משתפר משמעותית אם אומרים ל-Whisper אילו מונחים לצפות. בתיקיית
`course-packs/` יש רשימות מוכנות לכמה קורסים ב**האוניברסיטה העברית**:

| קורס | מונחים |
|---|---|
| 71811 אימונולוגיה כללית | 170 |
| 71453 תכונות פיזיקליות של מזונות | 81 |
| 71434 יחידות פעולה א׳ | 78 |
| 71204 שיטות בסיסיות בביולוגיה מולקולרית | 73 |
| 71219 מעבדה במיקרוביולוגיה יישומית | 62 |
| 71019 מבוא לכלכלה | 59 |

להשתמש: להעתיק את הקובץ הרלוונטי לתיקיית הקורס בשם `_style.md`.

**כדאי לדעת:** Whisper משתמש רק ב-223 טוקנים הראשונים של הרשימה, ועברית "יקרה"
בטוקנים. לכן המונחים החשובים ביותר צריכים להיות **בתחילת הרשימה**. הכלי מזהיר
כשהרשימה ארוכה מדי ואומר כמה מונחים בפועל ייכנסו.

---

## הפיכת התמלול להערות לימוד

זה החצי השני, והוא אופציונלי. **עובד עם כל עוזר AI** — ChatGPT, Gemini, Claude,
מה שנוח לכן. יש שתי דרכים:

### אם העוזר יכול לקרוא קבצים במחשב
(Claude Code, Gemini CLI, Cursor, Copilot בעורך)

פותחים את תיקיית ההערות ואומרים *"תמירי את ההרצאה החדשה בקורס 71811"*.
הוא קורא לבד את הכללים, את אוצר המילים ואת התמלול.

### אם זה צ'אט באתר
(ChatGPT, Gemini, Claude.ai)

```bash
lecture --prompt --course 71811 | pbcopy
```

מרכיב את הכללים שלכן, את המידע על הקורס ואת התמלול לבלוק אחד ומעתיק ללוח.
פשוט להדביק בצ'אט. זהו.

*(בלי `| pbcopy` זה פשוט מדפיס למסך.)*

שני קבצים שולטים בתוצאה:

- **`_instructions.md`** בשורש — איך ההערות אמורות להיראות. **מגיע ריק בכוונה.**
  זה הקובץ הכי חשוב במערכת, וכל אחת כותבת אותו לעצמה. שאלות מנחות בתוכו.
- **`<קורס>/_style.md`** — מה מיוחד בקורס הזה, אוצר המילים, וטבלת תיקוני תמלול.

**טבלת תיקוני התמלול** היא הרעיון שעושה את ההבדל: Whisper לפעמים משתבש גם עם
רשימת מונחים. במקום להילחם בזה, רושמים את השגיאה ואת הצורה הנכונה, והתיקון
נעשה בזמן כתיבת ההערות — דטרמיניסטי, לא הימור.

---

## פרטיות

הכול מקומי. ההקלטה לא עוזבת את המחשב, ואין צורך בחשבון, ב-API key או בחיבור
לאינטרנט (אחרי הורדת המודל).

---

## תרומה

יש לכן אוצר מילים לקורס שלא ברשימה? פתחו PR עם קובץ חדש ב-`course-packs/`,
או שלחו את הרשימה ואוסיף אותה. רשימה טובה נבנית מ**שגיאות אמיתיות** —
המונחים ש-Whisper משבש בקורס שלכן הם בדיוק אלה שצריך לרשום.

---

## מה יש כאן

```
transcribe.py            הכלי עצמו
setup.sh                 התקנה
vault-template/          תבנית לתיקיית ההערות
  _instructions.md       ריק — למילוי עצמי
  AI-ASSISTANT.md        הוראות לעוזר, לא משנה איזה
  CLAUDE.md              מצביע על הקובץ למעלה (Claude Code קורא אותו אוטומטית)
  _course-template/      תבנית לקורס חדש
course-packs/            אוצר מילים לקורסי HUJI
```

---

<details>
<summary><b>English</b></summary>

Local Hebrew lecture transcription for university students. Replaces NotebookLM
and similar cloud tools, which handle Hebrew poorly — especially English technical
terms spoken inside Hebrew sentences, where they produce mixed-script garbage and
spell the same term three different ways in one lecture.

Uses [ivrit-ai](https://huggingface.co/ivrit-ai)'s Hebrew-tuned Whisper via
faster-whisper. Runs entirely on your machine, roughly 4x realtime on Apple
Silicon. Nothing is uploaded, no account or API key needed.

**Install:** `bash setup.sh` (macOS with Homebrew; one-time 1.5 GB model download)

**Use:** `lecture --latest --course 71811`

Outputs a plain-text transcript and a timestamped `.srt` into a per-course folder.

Course vocabulary packs for several Hebrew University courses are in
`course-packs/` — feeding Whisper the terms it should expect measurably improves
accuracy. Note that only the first ~223 tokens of the list are used, and Hebrew
tokenizes inefficiently, so order matters; the tool warns you when a list
overflows.

The optional second half turns transcripts into study notes using **any AI assistant**
— ChatGPT, Gemini, Claude, whatever you already use. If your assistant can read local
files, point it at the folder. If it is a web chat, `lecture --prompt --course <n>`
assembles your rules, the course vocabulary and the transcript into one pasteable
block.

It is driven by an `_instructions.md` you write yourself, and it ships blank on
purpose — that file is the method, and it should be yours.

</details>
