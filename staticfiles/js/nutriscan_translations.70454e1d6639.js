/**
 * NutriScan — Client-side translations v2
 * =========================================
 * Place in: static/js/nutriscan_translations.js
 * Translates: data-i18n elements + <option> + <select> + JS-generated text
 */

const TRANSLATIONS = {
  en: {
    // Navbar
    "Analyze": "Analyze", "Dashboard": "Dashboard", "History": "History",
    "Profile": "Profile", "Admin": "Admin", "Sign out": "Sign out",
    // Landing
    "AI-powered food intelligence": "AI-powered food intelligence",
    "Know exactly what you eat.": "Know exactly what you eat.",
    "Sign in": "Sign in", "Create account": "Create account",
    "Welcome back": "Welcome back",
    "Sign in to your NutriScan account": "Sign in to your NutriScan account",
    "Get started": "Get started",
    "Create your free NutriScan account": "Create your free NutriScan account",
    "Username": "Username", "Password": "Password", "Confirm": "Confirm",
    "First name": "First name", "Email": "Email", "Admin panel": "Admin panel",
    // Profile
    "Set Up Your Profile": "Set Up Your Profile", "Edit Profile": "Edit Profile",
    "Body metrics": "Body metrics", "Lifestyle": "Lifestyle", "Medical flags": "Medical flags",
    "Setup steps": "Setup steps",
    "Used to compute your BMI and daily calorie target (TDEE).": "Used to compute your BMI and daily calorie target (TDEE).",
    "Age": "Age", "Biological sex": "Biological sex",
    "Height (cm)": "Height (cm)", "Weight (kg)": "Weight (kg)",
    "Live BMI estimate": "Live BMI estimate",
    "Fill height and weight above": "Fill height and weight above",
    "Activity level": "Activity level", "Health goal": "Health goal",
    "Medical & dietary flags": "Medical & dietary flags",
    "These affect your personalised score — high-risk items are flagged automatically.":
      "These affect your personalised score — high-risk items are flagged automatically.",
    "🩺 Diabetes": "🩺 Diabetes", "❤️ Hypertension": "❤️ Hypertension",
    "🌿 Vegetarian": "🌿 Vegetarian", "🌱 Vegan": "🌱 Vegan",
    "🌾 Gluten intolerant": "🌾 Gluten intolerant",
    "🥛 Lactose intolerant": "🥛 Lactose intolerant", "🥜 Nut allergy": "🥜 Nut allergy",
    "Next step →": "Next step →", "← Back": "← Back", "Save profile ✓": "Save profile ✓",
    "YOUR BMI": "YOUR BMI",
    // Activity levels
    "Sedentary (desk job, little exercise)": "Sedentary (desk job, little exercise)",
    "Lightly Active (1–3 days/week)": "Lightly Active (1–3 days/week)",
    "Moderately Active (3–5 days/week)": "Moderately Active (3–5 days/week)",
    "Very Active (6–7 days/week)": "Very Active (6–7 days/week)",
    "Athlete / Intense daily training": "Athlete / Intense daily training",
    // Health goals
    "Lose Weight": "Lose Weight", "Maintain Weight": "Maintain Weight",
    "Gain Muscle / Bulk": "Gain Muscle / Bulk",
    "Improve General Health": "Improve General Health",
    // BMI categories
    "Underweight": "Underweight", "Normal weight": "Normal weight",
    "Overweight": "Overweight", "Obese": "Obese", "OVERWEIGHT": "OVERWEIGHT",
    // Sex options
    "Male": "Male", "Female": "Female", "Prefer not to say": "Prefer not to say",
    // Analyze
    "food analysis": "food analysis", "What did you eat?": "What did you eat?",
    "Upload a photo, paste a link, or type the name. Our AI does the rest.":
      "Upload a photo, paste a link, or type the name. Our AI does the rest.",
    "Upload photo": "Upload photo", "Image URL": "Image URL", "Type name": "Type name",
    "Drop your food photo here": "Drop your food photo here",
    "or click to browse — JPG, PNG, WEBP up to 10 MB": "or click to browse — JPG, PNG, WEBP up to 10 MB",
    "Portion size": "Portion size",
    "Analyse this food →": "Analyse this food →", "Analysing…": "Analysing…",
    // Result
    "Identified food": "Identified food", "Alternative predictions": "Alternative predictions",
    "Score breakdown": "Score breakdown", "Full nutrition breakdown": "Full nutrition breakdown",
    "Data from USDA FoodData Central": "Data from USDA FoodData Central",
    "Recommended for you": "Recommended for you",
    "✓ Strengths": "✓ Strengths", "⚠ Watch out for": "⚠ Watch out for",
    "Analyse another food →": "Analyse another food →", "Delete entry": "Delete entry",
    "No notable strengths found.": "No notable strengths found.",
    "No concerns for your profile.": "No concerns for your profile.",
    // Dashboard
    "TOTAL ANALYSES": "TOTAL ANALYSES", "AVERAGE SCORE": "AVERAGE SCORE",
    "TODAY'S KCAL": "TODAY'S KCAL", "BMI": "BMI",
    "all time": "all time", "out of 10": "out of 10", "logged today": "logged today",
    "TODAY'S CALORIE BUDGET": "TODAY'S CALORIE BUDGET",
    "7-day calorie trend": "7-day calorie trend", "Score distribution": "Score distribution",
    "Recent analyses": "Recent analyses", "View all →": "View all →",
    "Most analysed": "Most analysed", "Your profile": "Your profile",
    "Goal": "Goal", "Activity": "Activity", "Daily target": "Daily target", "TDEE": "TDEE",
    "Edit profile": "Edit profile",
    "No food analysed yet.": "No food analysed yet.",
    "Start by scanning your first meal!": "Start by scanning your first meal!",
    "+ Analyse food": "+ Analyse food", "Analyse food →": "Analyse food →",
    "Complete your health profile": "Complete your health profile",
    "Complete profile →": "Complete profile →", "Good day,": "Good day,",
    // History
    "Food history": "Food history", "All scores": "All scores",
    "Filter": "Filter", "✕ Clear": "✕ Clear", "Search food name…": "Search food name…",
    "No entries match your filters.": "No entries match your filters.",
    "Clear filters": "Clear filters",
    // Scores
    "EXCELLENT": "EXCELLENT", "GOOD": "GOOD", "MODERATE": "MODERATE",
    "POOR": "POOR", "AVOID": "AVOID",
    "Excellent": "Excellent", "Good": "Good", "Moderate": "Moderate",
    "Poor": "Poor", "Avoid": "Avoid",
  },

  he: {
    // Navbar
    "Analyze": "ניתוח מזון", "Dashboard": "לוח בקרה", "History": "היסטוריה",
    "Profile": "פרופיל", "Admin": "ניהול", "Sign out": "התנתק",
    // Landing
    "AI-powered food intelligence": "בינה מלאכותית לזיהוי מזון",
    "Know exactly what you eat.": "דע בדיוק מה אתה אוכל.",
    "Sign in": "כניסה", "Create account": "הרשמה",
    "Welcome back": "ברוך שובך",
    "Sign in to your NutriScan account": "התחבר לחשבון NutriScan שלך",
    "Get started": "בוא נתחיל",
    "Create your free NutriScan account": "צור חשבון NutriScan חינמי",
    "Username": "שם משתמש", "Password": "סיסמה", "Confirm": "אימות סיסמה",
    "First name": "שם פרטי", "Email": "אימייל", "Admin panel": "פאנל ניהול",
    // Profile
    "Set Up Your Profile": "הגדרת פרופיל", "Edit Profile": "עריכת פרופיל",
    "Body metrics": "נתוני גוף", "Lifestyle": "אורח חיים", "Medical flags": "נתונים רפואיים",
    "Setup steps": "שלבי הגדרה",
    "Used to compute your BMI and daily calorie target (TDEE).": "לחישוב ה-BMI וצרכי הקלוריות היומיים שלך.",
    "Age": "גיל", "Biological sex": "מין ביולוגי",
    "Height (cm)": "גובה (ס\"מ)", "Weight (kg)": "משקל (ק\"ג)",
    "Live BMI estimate": "חישוב BMI חי",
    "Fill height and weight above": "הזן גובה ומשקל למעלה",
    "Activity level": "רמת פעילות גופנית", "Health goal": "יעד בריאותי",
    "Medical & dietary flags": "נתונים רפואיים ותזונתיים",
    "These affect your personalised score — high-risk items are flagged automatically.":
      "פרטים אלו משפיעים על הציון האישי שלך.",
    "🩺 Diabetes": "🩺 סוכרת", "❤️ Hypertension": "❤️ לחץ דם גבוה",
    "🌿 Vegetarian": "🌿 צמחוני", "🌱 Vegan": "🌱 טבעוני",
    "🌾 Gluten intolerant": "🌾 אי סבילות לגלוטן",
    "🥛 Lactose intolerant": "🥛 אי סבילות ללקטוז", "🥜 Nut allergy": "🥜 אלרגיה לאגוזים",
    "Next step →": "השלב הבא ←", "← Back": "→ חזרה", "Save profile ✓": "שמור פרופיל ✓",
    "YOUR BMI": "ה-BMI שלך",
    // Activity levels
    "Sedentary (desk job, little exercise)": "יושבני (עבודת משרד, מעט פעילות)",
    "Lightly Active (1–3 days/week)": "פעיל קלות (1-3 ימים/שבוע)",
    "Moderately Active (3–5 days/week)": "פעיל בינוני (3-5 ימים/שבוע)",
    "Very Active (6–7 days/week)": "פעיל מאוד (6-7 ימים/שבוע)",
    "Athlete / Intense daily training": "ספורטאי / אימון יומי אינטנסיבי",
    // Health goals
    "Lose Weight": "ירידה במשקל", "Maintain Weight": "שמירה על המשקל",
    "Gain Muscle / Bulk": "בניית שריר",
    "Improve General Health": "שיפור הבריאות הכללית",
    // BMI categories
    "Underweight": "תת משקל", "Normal weight": "משקל תקין",
    "Overweight": "עודף משקל", "Obese": "השמנת יתר", "OVERWEIGHT": "עודף משקל",
    // Sex options
    "Male": "זכר", "Female": "נקבה", "Prefer not to say": "מעדיף לא לציין",
    // Analyze
    "food analysis": "ניתוח מזון", "What did you eat?": "מה אכלת?",
    "Upload a photo, paste a link, or type the name. Our AI does the rest.":
      "העלה תמונה, הדבק קישור, או הקלד שם המזון. הבינה המלאכותית תעשה את השאר.",
    "Upload photo": "העלאת תמונה", "Image URL": "קישור לתמונה", "Type name": "הקלד שם",
    "Drop your food photo here": "גרור את תמונת המזון לכאן",
    "or click to browse — JPG, PNG, WEBP up to 10 MB": "או לחץ לבחירת קובץ",
    "Portion size": "גודל מנה",
    "Analyse this food →": "נתח מזון זה ←", "Analysing…": "מנתח...",
    // Result
    "Identified food": "מזון שזוהה", "Alternative predictions": "תחזיות חלופיות",
    "Score breakdown": "פירוט הציון", "Full nutrition breakdown": "פירוט תזונתי מלא",
    "Data from USDA FoodData Central": "נתונים ממאגר USDA",
    "Recommended for you": "מומלץ עבורך",
    "✓ Strengths": "✓ יתרונות", "⚠ Watch out for": "⚠ שים לב ל",
    "Analyse another food →": "נתח מזון נוסף ←", "Delete entry": "מחק רשומה",
    "No notable strengths found.": "לא נמצאו יתרונות בולטים.",
    "No concerns for your profile.": "אין התראות עבור הפרופיל שלך.",
    // Dashboard
    "TOTAL ANALYSES": "סה\"כ ניתוחים", "AVERAGE SCORE": "ציון ממוצע",
    "TODAY'S KCAL": "קלוריות היום", "BMI": "BMI",
    "all time": "כל הזמן", "out of 10": "מתוך 10", "logged today": "היום",
    "TODAY'S CALORIE BUDGET": "תקציב קלוריות להיום",
    "7-day calorie trend": "מגמת קלוריות - 7 ימים",
    "Score distribution": "התפלגות ציונים",
    "Recent analyses": "ניתוחים אחרונים", "View all →": "הצג הכל ←",
    "Most analysed": "מזונות נפוצים", "Your profile": "הפרופיל שלך",
    "Goal": "יעד", "Activity": "פעילות", "Daily target": "יעד יומי", "TDEE": "TDEE",
    "Edit profile": "ערוך פרופיל",
    "No food analysed yet.": "טרם נותח מזון.",
    "Start by scanning your first meal!": "התחל בסריקת הארוחה הראשונה שלך!",
    "+ Analyse food": "+ נתח מזון", "Analyse food →": "נתח מזון ←",
    "Complete your health profile": "השלם את הפרופיל הבריאותי שלך",
    "Complete profile →": "השלם פרופיל ←", "Good day,": "שלום,",
    // History
    "Food history": "היסטוריית מזון", "All scores": "כל הציונים",
    "Filter": "סינון", "✕ Clear": "✕ נקה", "Search food name…": "חפש שם מזון...",
    "No entries match your filters.": "לא נמצאו תוצאות.",
    "Clear filters": "נקה סינון",
    // Scores
    "EXCELLENT": "מעולה", "GOOD": "טוב", "MODERATE": "בינוני",
    "POOR": "חלש", "AVOID": "הימנע",
    "Excellent": "מעולה", "Good": "טוב", "Moderate": "בינוני",
    "Poor": "חלש", "Avoid": "הימנע",
  }
};

// ── Language Engine ────────────────────────────────────────────
const NutriLang = {

  current: localStorage.getItem('ns_lang') || 'en',

  init() {
    this.apply(this.current);
    this.updateButtons();
    this.updateDir();
  },

  set(lang) {
    this.current = lang;
    localStorage.setItem('ns_lang', lang);
    this.apply(lang);
    this.updateButtons();
    this.updateDir();
  },

  t(key) {
    return TRANSLATIONS[this.current]?.[key]
        || TRANSLATIONS['en']?.[key]
        || key;
  },

  apply(lang) {
    const dict = TRANSLATIONS[lang] || TRANSLATIONS['en'];

    // 1. Translate data-i18n elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const tr  = dict[key];
      if (!tr) return;
      if (el.tagName === 'INPUT' && el.hasAttribute('placeholder')) {
        el.placeholder = tr;
      } else {
        el.textContent = tr;
      }
    });

    // 2. Translate data-i18n-placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const tr  = dict[key];
      if (tr) el.placeholder = tr;
    });

    // 3. Translate <option> elements
    document.querySelectorAll('option').forEach(opt => {
      const original = opt.getAttribute('data-original') || opt.textContent.trim();
      if (!opt.getAttribute('data-original')) {
        opt.setAttribute('data-original', original);
      }
      const tr = dict[original];
      if (tr) opt.textContent = tr;
    });

    // 4. Translate card labels (health goal cards, etc.)
    document.querySelectorAll('.goal-card div[style*="font-weight:600"]').forEach(el => {
      const original = el.getAttribute('data-original') || el.textContent.trim();
      if (!el.getAttribute('data-original')) {
        el.setAttribute('data-original', original);
      }
      const tr = dict[original];
      if (tr) el.textContent = tr;
    });
  },

  updateButtons() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === this.current);
    });
  },

  updateDir() {
    document.documentElement.lang = this.current;
    document.documentElement.dir  = this.current === 'he' ? 'rtl' : 'ltr';
  }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => NutriLang.init());