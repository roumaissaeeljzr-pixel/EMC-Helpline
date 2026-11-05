export const translations = {
  fr: {
    common: {
      yes: "Oui",
      no: "Non",
      unknown: "Je ne sais pas",
      notProvided: "Non renseigné",
      continue: "Continuer",
      back: "Retour",
      restart: "Recommencer",
    },

    header: {
      statusAvailable: "Service disponible",
      statusUnavailable: "Service indisponible",
      languageFr: "FR",
      languageAr: "العربية",
    },

    navigation: {
      sectionVictim: "Espace victime",
      sectionAdmin: "Administration",

      dashboard: "Tableau de bord",
      assistant: "Assistant IA",
      assessment: "Évaluer ma situation",
      actionPlan: "Plan d'action",
      myCase: "Mon dossier",
      evidence: "Mes preuves",
      resources: "Ressources",
      history: "Historique",

      adminOverview: "Vue générale",
      adminStatistics: "Statistiques",
      adminCases: "Dossiers",
      adminPriorityCases: "Cas prioritaires",
      adminAiPerformance: "Performance IA",
      adminDocumentBase: "Base documentaire",
    },

    assistant: {
      title: "Assistant EMC Helpline",
      welcome:
        "Bonjour, je suis l’assistant EMC Helpline. Je peux vous aider à mieux comprendre votre situation et vous orienter à partir des informations disponibles.",
      placeholder: "Décrivez votre situation...",
      send: "Envoyer",
      loading: "Réponse en cours...",
      error:
        "Le service est momentanément indisponible. Veuillez réessayer dans quelques instants.",
      disclaimer:
        "EMC Helpline fournit des informations et une orientation à partir des ressources disponibles.",
    },

    assessment: {
      title: "Évaluer ma situation",
      intro:
        "Décrivez brièvement ce qui vous arrive. Cette évaluation permet d'identifier le type de situation et les informations éventuellement nécessaires pour mieux vous orienter.",
      descriptionLabel: "Description de la situation",
      placeholder: "Décrivez ce qui vous arrive...",
      submit: "Évaluer ma situation",
      loading: "Analyse en cours...",
      error:
        "Impossible d'évaluer la situation pour le moment. Veuillez réessayer.",

      result: {
        title: "Évaluation de votre situation",
        situationDetected: "Situation détectée",
        languageDetected: "Langue détectée : {language}",
        languageNameFr: "Français",
        languageNameAr: "Arabe",
        newEvaluation: "Nouvelle évaluation",
      },

      clarification: {
        title: "Une précision est nécessaire",
        ageQuestion:
          "Étiez-vous mineur(e) au moment où le contenu a été pris, ou étiez-vous déjà majeur(e) à ce moment-là ?",
        generic:
          "Une information complémentaire est nécessaire pour mieux orienter votre situation.",
      },

      emergency: {
        title: "Situation prioritaire détectée",
        message:
          "Cette situation nécessite une orientation immédiate vers une assistance humaine adaptée.",
      },
    },

    pages: {
      dashboard: {
        title: "Tableau de bord",
        description:
          "Cette page rassemblera votre dossier actif, votre plan d'action et vos accès rapides. Elle sera construite progressivement, au fur et à mesure que les modules de triage, dossier, preuves et plan d'action seront disponibles.",
        phase: "À développer — Phases 4 à 9",
      },
      actionPlan: {
        title: "Plan d'action",
        description:
          "Une liste d'actions personnalisées, construites à partir du corpus documentaire et de règles validées, avec suivi de progression.",
        phase: "À développer — Phase 5",
      },
      admin: {
        overview: {
          title: "Vue générale",
          description:
            "Vue d'ensemble de l'activité de la plateforme pour l'équipe EMC.",
          phase: "À développer — Phase 11",
        },
      },
    },
  },

  ar: {
    common: {
      yes: "نعم",
      no: "لا",
      unknown: "لا أعرف",
      notProvided: "غير محدد",
      continue: "متابعة",
      back: "رجوع",
      restart: "البدء من جديد",
    },

    header: {
      statusAvailable: "الخدمة متاحة",
      statusUnavailable: "الخدمة غير متاحة",
      languageFr: "FR",
      languageAr: "العربية",
    },

    navigation: {
      sectionVictim: "فضاء المستخدم",
      sectionAdmin: "الإدارة",

      dashboard: "لوحة التحكم",
      assistant: "المساعد الذكي",
      assessment: "تقييم وضعيتي",
      actionPlan: "خطة العمل",
      myCase: "ملفي",
      evidence: "أدلتي",
      resources: "الموارد",
      history: "السجل",

      adminOverview: "نظرة عامة",
      adminStatistics: "الإحصائيات",
      adminCases: "الملفات",
      adminPriorityCases: "الحالات ذات الأولوية",
      adminAiPerformance: "أداء الذكاء الاصطناعي",
      adminDocumentBase: "قاعدة الوثائق",
    },

    assistant: {
      title: "مساعد EMC Helpline",
      welcome:
        "مرحبًا، أنا مساعد EMC Helpline. يمكنني مساعدتك على فهم وضعيتك بشكل أفضل وتوجيهك بالاعتماد على المعلومات المتاحة.",
      placeholder: "صف وضعيتك...",
      send: "إرسال",
      loading: "جارٍ إعداد الرد...",
      error: "الخدمة غير متاحة مؤقتًا. يرجى المحاولة مرة أخرى بعد قليل.",
      disclaimer:
        "توفر EMC Helpline معلومات وتوجيهًا بالاعتماد على الموارد المتاحة.",
    },

    assessment: {
      title: "تقييم وضعيتي",
      intro:
        "صف بإيجاز ما يحدث لك. يساعد هذا التقييم على تحديد نوع الوضعية والمعلومات التي قد تكون ضرورية لتوجيهك بشكل أفضل.",
      descriptionLabel: "وصف الوضعية",
      placeholder: "صف ما يحدث لك...",
      submit: "تقييم وضعيتي",
      loading: "جارٍ تحليل الوضعية...",
      error: "تعذر تقييم الوضعية حاليًا. يرجى المحاولة مرة أخرى.",

      result: {
        title: "تقييم وضعيتك",
        situationDetected: "الوضعية المكتشفة",
        languageDetected: "اللغة المكتشفة: {language}",
        languageNameFr: "الفرنسية",
        languageNameAr: "العربية",
        newEvaluation: "تقييم جديد",
      },

      clarification: {
        title: "نحتاج إلى توضيح إضافي",
        ageQuestion:
          "هل كنت قاصرًا/قاصرة وقت التقاط المحتوى، أم كنت قد بلغت سن الرشد في ذلك الوقت؟",
        generic:
          "نحتاج إلى معلومة إضافية لتوجيه وضعيتك بشكل أفضل.",
      },

      emergency: {
        title: "تم رصد حالة ذات أولوية",
        message:
          "تتطلب هذه الحالة توجيهًا فوريًا نحو مساعدة بشرية مناسبة.",
      },
    },

    pages: {
      dashboard: {
        title: "لوحة التحكم",
        description:
          "ستجمع هذه الصفحة ملفك النشط وخطة عملك ووصولاً سريعًا إلى الأدوات. سيتم بناؤها تدريجيًا مع توفر وحدات الفرز والملف والأدلة وخطة العمل.",
        phase: "قيد التطوير — المراحل 4 إلى 9",
      },
      actionPlan: {
        title: "خطة العمل",
        description:
          "قائمة إجراءات مخصصة، مبنية على أساس قاعدة الوثائق والقواعد المعتمدة، مع تتبع للتقدم.",
        phase: "قيد التطوير — المرحلة 5",
      },
      admin: {
        overview: {
          title: "نظرة عامة",
          description: "نظرة شاملة على نشاط المنصة لفريق EMC.",
          phase: "قيد التطوير — المرحلة 11",
        },
      },
    },
  },
};