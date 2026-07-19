/**
 * Minimal i18n catalog for the launch languages.
 *
 * Six locales (Arabic is right-to-left). Strings cover the welcome shell,
 * experience launcher and the primary fan-app labels. Everything is keyed so
 * copy can be translated/extended without touching components.
 */

export type Locale = "en" | "es" | "fr" | "pt" | "ar" | "de";

export interface Strings {
  name: string;
  dir: "ltr" | "rtl";
  chooseLang: string;
  continue: string;
  chooseExp: string;
  fan: string;
  ops: string;
  maps: string;
  ai: string;
  fanDesc: string;
  opsDesc: string;
  mapsDesc: string;
  aiDesc: string;
  greet: string;
  liveAlerts: string;
  allClear: string;
  language: string;
  back: string;
}

export const LOCALES: Locale[] = ["en", "es", "fr", "pt", "ar", "de"];

export const I18N: Record<Locale, Strings> = {
  en: { name: "English", dir: "ltr", chooseLang: "Choose your language", continue: "Continue",
    chooseExp: "Choose an experience", fan: "Fan App", ops: "Operations Center", maps: "Stadium Map", ai: "AI Assistant",
    fanDesc: "Match info, wayfinding, alerts", opsDesc: "Heatmap, AI recommendations, incidents",
    mapsDesc: "Live congestion on the real ground", aiDesc: "Ask anything, get an explained answer",
    greet: "Good evening, welcome", liveAlerts: "Live alerts", allClear: "All clear — no congestion right now.",
    language: "Language", back: "Back" },
  es: { name: "Español", dir: "ltr", chooseLang: "Elige tu idioma", continue: "Continuar",
    chooseExp: "Elige una experiencia", fan: "App de Aficionado", ops: "Centro de Operaciones", maps: "Mapa del Estadio", ai: "Asistente IA",
    fanDesc: "Partido, orientación y alertas", opsDesc: "Mapa de calor, recomendaciones, incidentes",
    mapsDesc: "Congestión en vivo sobre el terreno", aiDesc: "Pregunta y recibe una respuesta explicada",
    greet: "Buenas noches, bienvenido", liveAlerts: "Alertas en vivo", allClear: "Todo despejado — sin congestión ahora.",
    language: "Idioma", back: "Atrás" },
  fr: { name: "Français", dir: "ltr", chooseLang: "Choisissez votre langue", continue: "Continuer",
    chooseExp: "Choisissez une expérience", fan: "Appli Supporter", ops: "Centre d'Opérations", maps: "Plan du Stade", ai: "Assistant IA",
    fanDesc: "Match, orientation et alertes", opsDesc: "Carte de chaleur, recommandations, incidents",
    mapsDesc: "Affluence en direct sur le terrain", aiDesc: "Posez une question, réponse expliquée",
    greet: "Bonsoir, bienvenue", liveAlerts: "Alertes en direct", allClear: "Tout est clair — aucune affluence.",
    language: "Langue", back: "Retour" },
  pt: { name: "Português", dir: "ltr", chooseLang: "Escolha o seu idioma", continue: "Continuar",
    chooseExp: "Escolha uma experiência", fan: "App do Torcedor", ops: "Central de Operações", maps: "Mapa do Estádio", ai: "Assistente IA",
    fanDesc: "Jogo, orientação e alertas", opsDesc: "Mapa de calor, recomendações, incidentes",
    mapsDesc: "Lotação ao vivo no terreno real", aiDesc: "Pergunte e receba uma resposta explicada",
    greet: "Boa noite, bem-vindo", liveAlerts: "Alertas ao vivo", allClear: "Tudo tranquilo — sem lotação agora.",
    language: "Idioma", back: "Voltar" },
  ar: { name: "العربية", dir: "rtl", chooseLang: "اختر لغتك", continue: "متابعة",
    chooseExp: "اختر تجربة", fan: "تطبيق المشجع", ops: "مركز العمليات", maps: "خريطة الملعب", ai: "المساعد الذكي",
    fanDesc: "معلومات المباراة والإرشاد والتنبيهات", opsDesc: "خريطة حرارية وتوصيات وحوادث",
    mapsDesc: "الازدحام المباشر على أرض الملعب", aiDesc: "اسأل أي شيء واحصل على إجابة موضحة",
    greet: "مساء الخير، أهلاً بك", liveAlerts: "تنبيهات مباشرة", allClear: "كل شيء هادئ — لا ازدحام الآن.",
    language: "اللغة", back: "رجوع" },
  de: { name: "Deutsch", dir: "ltr", chooseLang: "Wählen Sie Ihre Sprache", continue: "Weiter",
    chooseExp: "Erlebnis wählen", fan: "Fan-App", ops: "Leitstelle", maps: "Stadionplan", ai: "KI-Assistent",
    fanDesc: "Spielinfos, Wegführung, Hinweise", opsDesc: "Heatmap, KI-Empfehlungen, Vorfälle",
    mapsDesc: "Live-Andrang auf dem echten Gelände", aiDesc: "Fragen Sie – erklärte Antwort",
    greet: "Guten Abend, willkommen", liveAlerts: "Live-Hinweise", allClear: "Alles frei — derzeit kein Andrang.",
    language: "Sprache", back: "Zurück" },
};

/** Two-band SVG flag markup for a locale (no external image assets). */
export function flagColors(locale: Locale): [string, string] {
  const map: Record<Locale, [string, string]> = {
    en: ["#00247d", "#ffffff"], es: ["#aa151b", "#f1bf00"], fr: ["#0055a4", "#ef4135"],
    pt: ["#046a38", "#da291c"], ar: ["#006c35", "#ffffff"], de: ["#000000", "#dd0000"],
  };
  return map[locale];
}
