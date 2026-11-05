# -*- coding: utf-8 -*-
"""
generate_cyberharcelement_train_v1.py (v3 -- longueurs corrigées)

v2 avait une distribution de longueur très éloignée de la cible
(70 courtes / 13 moyennes / 17 longues au lieu de ~30/50/20), le
comptage manuel initial des mots arabes ayant été trop optimiste.
Cette version élargit substantiellement la majorité des phrases
initialement prévues "moyennes"/"longues" par des clauses
d'élaboration naturelles (délai, canal, conséquence, contexte),
en conservant le sens, le style et la famille de scenario_group.

3 groupes dépassaient également la taille maximale de 3 (taille 4) --
corrigés en sous-groupes distincts.

Toujours rédigé SANS ouverture d'AR-1/AR-2, sans appel à aucun modèle.
"""

import json
import re
import unicodedata
from pathlib import Path

OUTPUT_PATH = Path("data/arabic_training/source/cyberharcelement_train_candidates_v1.json")
LABEL = "Cyberharcèlement"

VALID_BOUNDARY_INTENTS = {
    "Cyberharcèlement", "Sextorsion", "Piratage de compte",
    "Divulgation de données personnelles (Doxing)", "Conservation des preuves",
    "Informations juridiques", "Usurpation d'identité",
    "Diffusion non consentie d'images", "Signalement",
    "Situation d'urgence", "Accompagnement de la victime",
}

# ============================================================
# DONNÉES : (text, style, boundary_with, group_label)
# ============================================================

ENTRIES_RAW: list[tuple[str, str, str | None, str]] = [

    # ---------------- DIRECT (20 : 6 courtes / 10 moyennes / 4 longues) ----------------

    # courtes (6)
    ("يواصل نفس الشخص إهانتي بألفاظ مسيئة كل يوم تقريبًا.", "direct", None, "generic_repeated_insults"),
    ("أتعرض لسخرية متكررة من نفس الشخص منذ أسابيع.", "direct", None, "generic_repeated_insults"),
    ("يهاجمني بكلمات مهينة في كل تعليق يكتبه.", "direct", None, "sarcastic_comment_each_post"),
    ("شخص واحد يهينني علنًا بشكل متكرر منذ مدة.", "direct", None, "generic_public_insults"),
    ("تكررت إهاناته لي دون أي سبب واضح.", "direct", None, "generic_public_insults"),
    ("يستمر في السخرية مني كلما نشرت شيئًا.", "direct", None, "sarcastic_comment_each_post"),

    # moyennes (10)
    ("منذ حوالي ثلاثة أسابيع، يواصل هذا الشخص إرسال رسائل مهينة لي بشكل شبه يومي، دون أن يتوقف رغم تجاهلي المتكرر له.", "direct", None, "private_messages_daily"),
    ("أتعرض لتعليقات ساخرة ومهينة بشكل متكرر أسفل كل منشور أنشره على حسابي، وقد أصبح ذلك أمرًا شبه ثابت منذ أسابيع.", "direct", None, "public_comments_embarrass"),
    ("شخص يهاجمني بألفاظ مسيئة في كل مرة أشارك فيها رأيي علنًا على الإنترنت، ويبدو أن الأمر يتكرر عمدًا في كل مناسبة.", "direct", None, "public_opinion_attacked"),
    ("منذ فترة طويلة، يقوم أحدهم بإذلالي علنًا عبر التعليقات في كل مناسبة تقريبًا، دون أن يتغير هذا السلوك رغم مرور الوقت.", "direct", None, "public_comments_embarrass"),
    ("يرسل لي رسائل ساخرة ومهينة بشكل متكرر، ويبدو أنه يستمتع بإحراجي أمام الآخرين، وهذا يحدث الآن بشكل شبه يومي.", "direct", None, "private_messages_daily"),
    ("أتلقى يوميًا رسائل تحقير من نفس الشخص منذ أن انضممت إلى هذا المنتدى قبل شهر تقريبًا، دون أن يتوقف هذا السلوك حتى الآن.", "direct", None, "forum_context"),
    ("يستمر أحد الأعضاء في السخرية مني وإهانتي علنًا في كل نقاش أشارك فيه تقريبًا، وأصبح الأمر متوقعًا في كل مرة أفتح فيها المنتدى.", "direct", None, "forum_context"),
    ("تكررت محاولاته لإحراجي وإهانتي عبر التعليقات العامة أكثر من مرة خلال هذا الأسبوع وحده، وهو ما يجعلني أشعر أن الأمر متعمد تمامًا.", "direct", None, "public_comments_embarrass_b"),
    ("يهينني بشكل متكرر أمام زملائي داخل مجموعة العمل الرقمية منذ عدة أسابيع متتالية، رغم أنني حاولت تجاهل تعليقاته أكثر من مرة.", "direct", None, "work_colleagues_present"),
    ("أصبحت أتوقع رسالة مهينة منه كل صباح تقريبًا دون أي استثناء يُذكر، وقد استمر هذا الأمر منذ ما يقارب الشهر الآن.", "direct", None, "private_messages_morning"),

    # longues (4)
    ("بدأ الأمر منذ حوالي شهرين حين علّق أحدهم بسخرية على أحد منشوراتي، ثم تحول ذلك سريعًا إلى نمط متكرر من الإهانات اليومية التي لم تتوقف حتى الآن رغم تجاهلي المتكرر له ومحاولاتي المتعددة لعدم الرد على تعليقاته.", "direct", None, "escalation_from_comment"),
    ("منذ أن بدأت أستخدم هذا الحساب بانتظام قبل بضعة أشهر، لاحظت أن الشخص نفسه يعلّق بشكل مهين على كل ما أنشره تقريبًا، وقد تكرر ذلك عشرات المرات خلال الأسابيع الماضية دون أي مبرر واضح يفسر إصراره على الاستمرار.", "direct", None, "public_comments_embarrass_b"),
    ("في البداية ظننت أن الأمر مجرد تعليق عابر لا يستحق الاهتمام، لكن مع تكرار الإهانات من نفس الشخص أسبوعًا بعد أسبوع، أدركت أن ما يحدث هو نمط ثابت من الاستهداف المتعمد الذي لا يبدو أنه سيتوقف قريبًا مهما فعلت لتجاهله.", "direct", None, "escalation_from_comment"),
    ("يرسل لي هذا الشخص رسائل مهينة منذ ما يقارب الشهر، وفي كل مرة أحاول تجاهله يعود بتعليق أكثر حدة من السابق، وأصبح الأمر متكررًا لدرجة أنني بدأت أتوقعه في كل مرة أفتح فيها التطبيق صباحًا أو مساءً.", "direct", None, "private_messages_morning"),

    # ---------------- INDIRECT (20 : 6 courtes / 11 moyennes / 3 longues) ----------------

    # courtes (6)
    ("أصبحت الهدف الدائم لسخرية نفس الشخص مؤخرًا.", "indirect", None, "fixed_target_short"),
    ("يُسخر مني علنًا كلما نشرت شيئًا جديدًا.", "indirect", None, "targeted_after_each_post"),
    ("توقفت عن المشاركة بسبب استهدافي المتكرر هناك.", "indirect", None, "avoidance_behavior"),
    ("أصبح الآخرون يضحكون عليّ أمام الجميع كلما شاركت في نقاش داخل المجموعة.", "indirect", None, "fixed_target_short"),
    ("أُستهدف بانتظام بعد كل منشور أكتبه هناك.", "indirect", None, "targeted_after_each_post"),
    ("بت أتجنب النشر خوفًا من السخرية المعتادة.", "indirect", None, "avoidance_behavior"),

    # moyennes (11)
    ("منذ فترة، أصبحت الشخص الذي يُسخر منه علنًا في كل مرة يظهر فيها اسمي على الشاشة، وهذا بدأ يتكرر بشكل شبه يومي.", "indirect", None, "fixed_target_medium"),
    ("لاحظت أنني أصبحت هدفًا ثابتًا للسخرية العلنية في كل مرة أشارك فيها بأي رأي، وأصبح الأمر متوقعًا مهما كان موضوع النقاش.", "indirect", None, "fixed_target_medium"),
    ("توقفت تمامًا عن المشاركة في المجموعة بسبب تكرار استهدافي فيها أسبوعًا بعد أسبوع، رغم أنني كنت أشارك فيها بانتظام من قبل.", "indirect", None, "avoidance_behavior_b"),
    ("أصبح ظهور اسمي في أي منشور كافيًا ليجذب موجة من التعليقات الساخرة الموجهة لي تحديدًا، وهذا يحدث الآن في كل مرة تقريبًا.", "indirect", None, "targeted_after_each_post_b"),
    ("لم أعد أشارك بحرية لأن كل تعليق أكتبه يقابله رد يهدف إلى إضحاك الآخرين علي، وقد أصبح هذا نمطًا واضحًا منذ فترة.", "indirect", None, "ridicule_public_exposure"),
    ("أصبحت أُعرض للسخرية أمام مجموعة كاملة من الأشخاص كلما تحدثت في أي نقاش عام، وهذا يحدث بانتظام منذ عدة أسابيع الآن.", "indirect", None, "public_discussion_exposure"),
    ("بدأت أتجنب فتح التطبيق لأن ظهوري فيه يعني تلقائيًا موجة جديدة من التعليقات الساخرة، وأصبح هذا التوقع جزءًا من روتيني اليومي.", "indirect", None, "avoidance_fear_of_reaction"),
    ("أصبح اسمي مرتبطًا بنكتة متكررة يرددها نفس الأشخاص كلما نشرت أي شيء، وهذا يتكرر منذ ما يقارب الشهرين دون أي تغيير.", "indirect", None, "ridicule_public_exposure"),
    ("توقفت عن التعبير عن رأيي بعدما أصبحت هدفًا ثابتًا للتعليقات الساخرة المتكررة، رغم أنني كنت أشارك بحرية أكبر في السابق.", "indirect", None, "avoidance_behavior_b"),
    ("لاحظت أن نفس الأشخاص يتحينون كل منشور لي لتوجيه سخريتهم نحوي علنًا، وأصبح هذا السلوك متوقعًا في كل مرة أنشر فيها شيئًا.", "indirect", None, "targeted_after_each_post_b"),
    ("أصبحت أُقصى تدريجيًا من النقاشات بسبب تكرار السخرية الموجهة لي هناك، وهذا جعلني أبتعد شيئًا فشيئًا عن المشاركة كليًا.", "indirect", None, "public_discussion_exposure"),

    # longues (3)
    ("في البداية لم ألاحظ الأمر بوضوح، لكن مع الوقت أدركت أنني أصبحت الهدف المفضل للسخرية في كل مرة أظهر فيها في أي نقاش، لدرجة أنني بدأت أتجنب المشاركة كليًا تجنبًا لتكرار الموقف نفسه مرارًا وتكرارًا.", "indirect", None, "public_discussion_exposure"),
    ("منذ أن انضممت إلى هذه المساحة الرقمية قبل بضعة أشهر، لاحظت أن كل تعليق أكتبه يقابل برد ساخر من نفس الأشخاص، حتى أصبحت أخشى المشاركة لأن النتيجة أصبحت متوقعة تمامًا في كل مرة أحاول فيها التفاعل بشكل طبيعي.", "indirect", None, "ridicule_public_exposure"),
    ("بدأ الأمر بتعليقات عابرة لم أعرها اهتمامًا في البداية، لكن مع تكرارها أسبوعًا بعد أسبوع أدركت أنني أصبحت هدفًا ثابتًا لسخرية جماعية تظهر في كل مرة أشارك فيها بأي محتوى، مما دفعني إلى التوقف عن النشر تمامًا منذ فترة.", "indirect", None, "escalation_realization"),

    # ---------------- CONTEXTUAL (20 : 4 courtes / 12 moyennes / 4 longues) ----------------

    # courtes (4)
    ("زملائي في الفصل يسخرون مني في مجموعة الواتساب باستمرار.", "contextual", None, "classmates_whatsapp_group"),
    ("في مساحة العمل الرقمية، يتعمد بعض الزملاء استبعادي من النقاش ثم يسخرون مني كلما حاولت المشاركة.", "contextual", None, "work_team_exclusion"),
    ("لاعبون آخرون يستهدفونني بإهانات متكررة أثناء كل مباراة.", "contextual", None, "gaming_match_insults"),
    ("أخبرتني زميلة أن مجموعة من الطلاب تتداول عني تعليقات ساخرة باستمرار داخل المجموعة الدراسية.", "contextual", None, "told_by_colleague_group"),

    # moyennes (12)
    ("في مجموعة الفصل على واتساب، يتناوب عدة زملاء على السخرية من إجاباتي كلما شاركت شيئًا، وهذا أصبح شبه يومي منذ بداية الفصل.", "contextual", None, "study_group_mocking_answers"),
    ("أخبرني صديق أن اسمي أصبح موضع نكات متكررة داخل قناة العمل المشتركة على Telegram، وأن هذا يحدث بانتظام منذ عدة أسابيع.", "contextual", None, "work_channel_named_jokes"),
    ("خلال الجولات الجماعية في إحدى الألعاب، يتفق أكثر من لاعب على إهانتي بشكل متكرر، وقد أصبح هذا الأمر متوقعًا في بداية كل جولة.", "contextual", None, "gaming_match_insults"),
    ("لاحظت أن أعضاء المنتدى الجامعي يتجاهلون مساهماتي عمدًا ويسخرون منها كلما شاركت رأيًا، وهذا السلوك مستمر منذ عدة أسابيع تقريبًا.", "contextual", None, "university_forum_ignored"),
    ("بدأت شائعات ساخرة عني تنتشر داخل مجموعة الحي على فيسبوك دون أي سبب حقيقي، وأصبح الأمر يتكرر في كل نقاش عام يخص المجموعة.", "contextual", None, "neighborhood_rumors"),
    ("في اجتماعات الفريق الافتراضية الأخيرة، وجّه لي أكثر من زميل تعليقات جارحة أمام الجميع، وهذا يحدث الآن بشكل شبه ثابت في كل اجتماع.", "contextual", None, "virtual_meetings_multiple"),
    ("أصبحت مادة للسخرية المتكررة داخل مجموعة الدراسة على Discord كلما طرحت سؤالًا، وهذا جعلني أتردد كثيرًا قبل المشاركة في أي نقاش.", "contextual", None, "study_group_mocking_answers"),
    ("يتناوب مشاهدون مختلفون على إهانتي في كل بث مباشر أقدمه لمجتمع الألعاب، وأصبح هذا السلوك متوقعًا في كل مرة أبدأ فيها البث.", "contextual", None, "gaming_livestream_viewers"),
    ("داخل مجتمع المبرمجين الذي أنتمي إليه، تتكرر السخرية من أفكاري من نفس مجموعة الأشخاص، وهذا يحدث في كل مرة أشارك فيها اقتراحًا جديدًا.", "contextual", None, "professional_community_mocking"),
    ("أُخبرت أن هناك من ينشر تعليقات مهينة عني في مجموعة الزمالة كلما غبت عنها، وهذا الأمر مستمر منذ فترة دون أن أدرك ذلك.", "contextual", None, "work_channel_named_jokes"),
    ("خلال نقاشات النادي الأدبي الرقمي، يواصل أكثر من عضو التقليل من كتاباتي بطريقة جارحة، وأصبح هذا السلوك متكررًا في كل جلسة نقاش.", "contextual", None, "professional_community_mocking"),
    ("في غرفة الدردشة الخاصة بالمشروع، تحول اسمي إلى موضوع تعليقات ساخرة متكررة بين الزملاء، وهذا بدأ يؤثر على راحتي أثناء العمل.", "contextual", None, "virtual_meetings_multiple"),

    # longues (4)
    ("منذ انضمامي إلى مجموعة العمل التطوعي قبل بضعة أشهر، بدأ بعض الأعضاء يتناوبون على توجيه انتقادات مهينة لي في كل اجتماع افتراضي، وتطور الأمر تدريجيًا حتى أصبح شبه ثابت في كل نقاش جماعي نشارك فيه بغض النظر عن الموضوع المطروح.", "contextual", None, "work_team_exclusion"),
    ("في بداية انضمامي إلى النادي الرياضي الرقمي، شعرت بالترحيب، لكن مع مرور الوقت بدأ بعض الأعضاء يتفقون ضمنيًا على السخرية من كل تعليق أكتبه، حتى أصبح الأمر نمطًا متكررًا يتكرر في كل مرة أظهر فيها هناك بشكل شبه منتظم.", "contextual", None, "sports_club_gradual"),
    ("أخبرتني زميلة أن هناك مجموعة صغيرة داخل الفصل الدراسي تتبادل تعليقات ساخرة عني بانتظام عبر واتساب، وأن الأمر لم يعد يقتصر على مرة واحدة بل أصبح شبه يومي منذ عدة أسابيع، دون أن أكون على علم بذلك في البداية.", "contextual", None, "told_by_colleague_group"),
    ("خلال مشاركتي المتكررة في مجتمع الألعاب عبر الإنترنت، لاحظت أن نفس المجموعة من اللاعبين تتعمد استهدافي بتعليقات مهينة في بداية كل جولة، وأصبح الأمر متوقعًا لدرجة أنني بدأت أتردد كثيرًا في الانضمام مجددًا إلى أي جولة جديدة.", "contextual", None, "gaming_livestream_viewers"),

    # ---------------- PARAPHRASE (20 : 6 courtes / 11 moyennes / 3 longues) ----------------

    # courtes (6)
    ("أصبحت هدفًا متكررًا لإذلال ممنهج من طرف واحد.", "paraphrase", None, "fixed_target_no_justification"),
    ("يمارس ضدي نمطًا واضحًا من التحقير المتكرر.", "paraphrase", None, "habitual_degrading_behavior"),
    ("لاحظت نمطًا ثابتًا من الاستهداف المتعمد ضدي.", "paraphrase", None, "clear_pattern_targeting"),
    ("أصبح تحقيري سلوكًا معتادًا يمارسه بانتظام.", "paraphrase", None, "habitual_degrading_behavior"),
    ("أعيش حالة متكررة من الاستهزاء غير المبرر.", "paraphrase", None, "clear_pattern_targeting"),
    ("استمرار إهانته لي جعلني هدفًا دائمًا له.", "paraphrase", None, "fixed_target_no_justification"),

    # moyennes (11)
    ("أجد نفسي مستهدفًا بشكل متكرر من طرف واحد يصر على التقليل من قيمتي علنًا أمام الجميع، دون أي مبرر حقيقي يفسر إصراره.", "paraphrase", None, "systematic_targeting"),
    ("ما يحدث لي هو نمط متكرر من الإذلال الرقمي الذي لم يتوقف منذ عدة أسابيع متتالية، رغم كل محاولاتي لتجاهل الأمر برمته.", "paraphrase", None, "humiliation_pattern"),
    ("أصبحت عرضة لسلوك ممنهج من التحقير يمارسه نفس الشخص كلما سنحت له الفرصة، وهذا يحدث الآن بشكل شبه منتظم منذ فترة.", "paraphrase", None, "systematic_targeting"),
    ("يبدو أن هدفه الأساسي هو النيل مني علنًا كلما ظهرت فرصة مناسبة على الإنترنت، وهذا الأمر يتكرر منذ ما يقارب الشهر تقريبًا.", "paraphrase", None, "opportunistic_targeting"),
    ("أعاني من تكرار مستمر لمواقف الإذلال الموجهة لي تحديدًا من الطرف نفسه، وقد أصبح هذا جزءًا شبه ثابت من تفاعلاتي على الإنترنت.", "paraphrase", None, "pattern_not_isolated"),
    ("يتكرر إحراجي أمام الآخرين بطريقة تبدو مدروسة ومقصودة تمامًا من جانبه، وهذا يحدث في كل مرة تقريبًا دون أي استثناء يُذكر.", "paraphrase", None, "deliberate_embarrassment"),
    ("ما يفعله ليس حادثة معزولة، بل نمط متكرر من الاستفزاز والتحقير المباشر الذي يستمر منذ فترة طويلة نسبيًا دون أي بادرة للتوقف.", "paraphrase", None, "pattern_not_isolated"),
    ("أشعر أنني أصبحت هدفًا ثابتًا لسخريته المتكررة دون أي مبرر منطقي يفسر هذا السلوك المستمر منذ عدة أسابيع حتى الآن.", "paraphrase", None, "fixed_target_repeated_sarcasm"),
    ("يواظب على إظهاري بمظهر سيئ أمام الآخرين كلما أتيحت له الفرصة لذلك، وهذا السلوك أصبح متوقعًا منه في كل تفاعل تقريبًا.", "paraphrase", None, "opportunistic_targeting"),
    ("أصبح تحقيري جزءًا متكررًا من تفاعله معي منذ فترة ليست بالقصيرة، رغم أنني حاولت أكثر من مرة تجاهل الأمر بالكامل.", "paraphrase", None, "repeated_interaction_pattern"),
    ("لاحظت نمطًا واضحًا من الاستهداف المتكرر يمارسه ضدي دون أي توقف يُذكر، وهذا جعلني أشعر أنني أصبحت هدفًا دائمًا له.", "paraphrase", None, "clear_pattern_realization"),

    # longues (3)
    ("بدأ الأمر بتعليق واحد لم أعره اهتمامًا، لكنه تحول تدريجيًا إلى نمط متكرر من التحقير الممنهج الذي يمارسه ضدي نفس الشخص في كل مناسبة تقريبًا، حتى أصبحت أتوقعه في كل تفاعل بيننا مهما كان السياق أو الموضوع المطروح.", "paraphrase", None, "humiliation_pattern"),
    ("منذ أن بدأ هذا السلوك قبل بضعة أسابيع، لاحظت أنه ليس مجرد ردود فعل عابرة، بل أسلوب متكرر ومقصود يهدف إلى إضعافي وإحراجي أمام من يشاهدون تفاعلاتي، وقد استمر هذا النمط دون أي تغيير يُذكر حتى وقتنا الحالي.", "paraphrase", None, "repeated_interaction_pattern"),
    ("أصبح واضحًا لي مع مرور الوقت أن ما أتعرض له ليس مجرد خلاف عابر، بل نمط ثابت من الاستهزاء المتعمد الذي يتكرر أسبوعًا بعد أسبوع دون أي محاولة حقيقية منه للتوقف، رغم كل الإشارات التي أعطيتها له لإنهاء الأمر.", "paraphrase", None, "clear_pattern_realization"),

    # ---------------- BOUNDARY (20 : 8 courtes / 6 moyennes / 6 longues) ----------------

    # Accompagnement de la victime (6)
    ("الإهانات المتكررة بدأت تستنزفني نفسيًا بشكل واضح.", "boundary", "Accompagnement de la victime", "psych_impact_exhaustion"),
    ("أصبحت مرهقة نفسيًا بسبب تكرار هذه الإهانات.", "boundary", "Accompagnement de la victime", "psych_impact_exhaustion"),
    ("لم أعد أشعر بنفس الحماس تجاه أي شيء بعدما أصبحت هدفًا متكررًا للسخرية المهينة منذ عدة أسابيع.", "boundary", "Accompagnement de la victime", "psych_impact_focus_loss"),
    ("تراكم الإهانات المتكررة من نفس الشخص جعلني أفقد تركيزي في أمور كثيرة أخرى، وهذا يزعجني بشكل متزايد.", "boundary", "Accompagnement de la victime", "psych_impact_focus_loss"),
    ("في البداية حاولت تجاهل الأمر، لكن مع تكرار الإهانات أسبوعًا بعد أسبوع، بدأت ألاحظ أنني أصبحت أكثر توترًا وأقل رغبة في التفاعل مع أي شخص، حتى خارج الإنترنت وفي حياتي اليومية بشكل عام.", "boundary", "Accompagnement de la victime", "psych_impact_escalation"),
    ("لم أتوقع أن تعليقات متفرقة تتحول مع الوقت إلى عبء نفسي حقيقي، فقد أصبحت أفكر في الأمر حتى عندما لا أكون متصلة بالإنترنت، وهذا بدأ يؤثر على نومي ومزاجي بشكل عام خلال الأسابيع الأخيرة.", "boundary", "Accompagnement de la victime", "psych_impact_escalation"),

    # Signalement (4)
    ("بدأت أفكر جديًا في اتخاذ خطوة رسمية بخصوص هذه الإهانات المتكررة.", "boundary", "Signalement", "considering_formal_action_short"),
    ("منذ أسابيع يلاحقني هذا الشخص بتعليقات ساخرة تحت منشوراتي، وبدأت أفكر في اتخاذ إجراء رسمي بحقه.", "boundary", "Signalement", "considering_formal_action_short"),
    ("بعد أسابيع من تحمل هذه الإهانات المتكررة من نفس الشخص، بت أفكر أن الوقت حان لفعل شيء حيال ذلك بشكل أكثر جدية.", "boundary", "Signalement", "considering_formal_action_medium"),
    ("لم أكن أتخيل أن الأمر سيستمر كل هذه المدة، فمنذ أن بدأت هذه الإهانات المتكررة، حاولت تجاهلها في البداية، لكنها الآن وصلت إلى نقطة أشعر فيها أنه ربما حان وقت التصرف بجدية أكبر تجاه هذا الشخص وسلوكه المتكرر.", "boundary", "Signalement", "considering_formal_action_medium"),

    # Situation d'urgence (4) -- reste non urgent
    ("إهاناته المتكررة تزعجني رغم عدم وجود أي خطر مباشر.", "boundary", "Situation d'urgence", "no_immediate_danger_short"),
    ("أتلقى تعليقات مهينة متكررة عبر الإنترنت، والوضع يزعجني نفسيًا لكن لا يوجد خطر مباشر حاليًا.", "boundary", "Situation d'urgence", "no_immediate_danger_short"),
    ("أشعر بانزعاج شديد من الإهانات المتكررة، لكن لا يوجد حتى الآن أي تهديد فعلي بالأذى من هذا الشخص.", "boundary", "Situation d'urgence", "no_immediate_danger_medium"),
    ("رغم أن هذا الشخص يواصل إهانتي بألفاظ قاسية بشكل شبه يومي، إلا أن الأمر يقتصر حتى الآن على الكلام المسيء فقط، دون أي إشارة إلى تهديد مباشر أو خطر جسدي وشيك من جانبه.", "boundary", "Situation d'urgence", "no_immediate_danger_medium"),

    # Conservation des preuves (3)
    ("بدأت أحفظ لقطات شاشة لكل رسالة مهينة يرسلها.", "boundary", "Conservation des preuves", "evidence_preservation"),
    ("منذ بداية هذه الإهانات المتكررة، أصبحت أوثق كل تعليق يكتبه لي تحسبًا لأي تطور لاحق قد يحدث.", "boundary", "Conservation des preuves", "evidence_preservation"),
    ("بعدما أدركت أن الإهانات لن تتوقف قريبًا، قررت أن أبدأ بتوثيق كل رسالة وتعليق يصلني من هذا الشخص، فقط احتياطًا في حال احتجت إلى الرجوع إليها لاحقًا لأي سبب كان.", "boundary", "Conservation des preuves", "evidence_preservation"),

    # Informations juridiques (3)
    ("منذ أسابيع أتلقى إهانات متكررة عبر الرسائل، وأتساءل أحيانًا إن كان هذا السلوك يخالف القانون.", "boundary", "Informations juridiques", "legal_question_secondary"),
    ("الإهانات المتكررة التي أتلقاها جعلتني أفكر فيما إذا كان لهذا السلوك أي تبعات قانونية محتملة في حالتي.", "boundary", "Informations juridiques", "legal_question_secondary"),
    ("مع استمرار هذه الإهانات المتكررة من نفس الشخص لأسابيع، بدأت أتساءل، دون أن أتخذ أي قرار بعد، عمّا إذا كان هذا النوع من السلوك يدخل ضمن ما يعاقب عليه القانون في حالات مشابهة لحالتي.", "boundary", "Informations juridiques", "legal_question_secondary"),
]


def build_dataset() -> list[dict]:

    assert len(ENTRIES_RAW) == 100, f"Attendu 100 entrées brutes, obtenu {len(ENTRIES_RAW)}"

    group_label_to_number: dict[str, int] = {}
    next_group_number = 1

    entries = []

    for index, (text, style, boundary_with, group_label) in enumerate(ENTRIES_RAW, start=1):

        if group_label not in group_label_to_number:
            group_label_to_number[group_label] = next_group_number
            next_group_number += 1

        group_number = group_label_to_number[group_label]

        entries.append({
            "id": f"train_ar_cyberharcelement_{index:04d}",
            "text": text,
            "label": LABEL,
            "style": style,
            "boundary_with": boundary_with,
            "scenario_group": f"cyber_scenario_{group_number:04d}",
        })

    return entries


def validate_structure(entries: list[dict]) -> None:

    assert len(entries) == 100, f"Attendu 100, obtenu {len(entries)}"
    ids = [e["id"] for e in entries]
    assert len(set(ids)) == 100, "IDs non uniques"
    assert all(e["label"] == LABEL for e in entries)

    style_counts: dict[str, int] = {}
    for e in entries:
        style_counts[e["style"]] = style_counts.get(e["style"], 0) + 1
    expected_styles = {"direct": 20, "indirect": 20, "contextual": 20, "paraphrase": 20, "boundary": 20}
    assert style_counts == expected_styles, f"Distribution styles incorrecte : {style_counts}"

    boundary_counts: dict[str, int] = {}
    for e in entries:
        if e["style"] == "boundary":
            boundary_counts[e["boundary_with"]] = boundary_counts.get(e["boundary_with"], 0) + 1
    expected_boundary = {
        "Accompagnement de la victime": 6, "Signalement": 4,
        "Situation d'urgence": 4, "Conservation des preuves": 3,
        "Informations juridiques": 3,
    }
    assert boundary_counts == expected_boundary, f"Distribution boundary incorrecte : {boundary_counts}"

    assert all(e["boundary_with"] is None for e in entries if e["style"] != "boundary")
    for e in entries:
        if e["boundary_with"] is not None:
            assert e["boundary_with"] in VALID_BOUNDARY_INTENTS
    for e in entries:
        assert set(e.keys()) == {"id", "text", "label", "style", "boundary_with", "scenario_group"}
        assert e["scenario_group"]


def word_count(text: str) -> int:
    return len(text.split())


def compute_length_distribution(entries: list[dict]) -> dict:
    short = [e for e in entries if word_count(e["text"]) < 15]
    medium = [e for e in entries if 15 <= word_count(e["text"]) <= 30]
    long_ = [e for e in entries if word_count(e["text"]) > 30]
    return {
        "short (<15)": len(short), "medium (15-30)": len(medium), "long (>30)": len(long_),
        "short_ids": [e["id"] for e in short], "medium_ids": [e["id"] for e in medium], "long_ids": [e["id"] for e in long_],
    }


ARABIC_DIACRITICS_PATTERN = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]"
)


def normalize_arabic_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = ARABIC_DIACRITICS_PATTERN.sub("", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def tokenize(text: str) -> set[str]:
    return set(normalize_arabic_text(text).split())


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


def check_internal_similarity(entries: list[dict], threshold: float = 0.5) -> dict:
    exact_dupes, normalized_dupes, jaccard_pairs = [], [], []
    seen_exact: dict[str, str] = {}
    seen_normalized: dict[str, str] = {}
    normalized_texts = {e["id"]: normalize_arabic_text(e["text"]) for e in entries}
    token_sets = {e["id"]: tokenize(e["text"]) for e in entries}

    for e in entries:
        if e["text"] in seen_exact:
            exact_dupes.append((seen_exact[e["text"]], e["id"]))
        else:
            seen_exact[e["text"]] = e["id"]
        norm = normalized_texts[e["id"]]
        if norm in seen_normalized:
            normalized_dupes.append((seen_normalized[norm], e["id"]))
        else:
            seen_normalized[norm] = e["id"]

    ids = [e["id"] for e in entries]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            id_a, id_b = ids[i], ids[j]
            sim = jaccard_similarity(token_sets[id_a], token_sets[id_b])
            if sim >= threshold:
                jaccard_pairs.append((id_a, id_b, round(sim, 3)))

    return {"exact_dupes": exact_dupes, "normalized_dupes": normalized_dupes, "jaccard_pairs": jaccard_pairs}


def compute_scenario_group_stats(entries: list[dict]) -> dict:
    groups: dict[str, list[str]] = {}
    for e in entries:
        groups.setdefault(e["scenario_group"], []).append(e["id"])
    sizes = [len(v) for v in groups.values()]
    size_distribution = {1: 0, 2: 0, 3: 0}
    for s in sizes:
        size_distribution[s] = size_distribution.get(s, 0) + 1
    return {
        "unique_groups": len(groups), "size_distribution": size_distribution,
        "min_size": min(sizes) if sizes else 0, "max_size": max(sizes) if sizes else 0,
        "avg_size": round(sum(sizes) / len(sizes), 2) if sizes else 0, "groups": groups,
    }


def main() -> None:
    entries = build_dataset()
    validate_structure(entries)

    similarity = check_internal_similarity(entries)
    scenario_stats = compute_scenario_group_stats(entries)
    length_stats = compute_length_distribution(entries)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"Fichier écrit : {OUTPUT_PATH}")
    print(f"Total : {len(entries)}")
    print()
    print("=== LONGUEUR ===")
    print(f"  courtes (<15 mots)   : {length_stats['short (<15)']}")
    print(f"  moyennes (15-30)     : {length_stats['medium (15-30)']}")
    print(f"  longues (>30)        : {length_stats['long (>30)']}")
    print()
    print("=== SCENARIO_GROUP ===")
    print(f"  groupes uniques : {scenario_stats['unique_groups']}")
    print(f"  taille 1 : {scenario_stats['size_distribution'].get(1, 0)}")
    print(f"  taille 2 : {scenario_stats['size_distribution'].get(2, 0)}")
    print(f"  taille 3 : {scenario_stats['size_distribution'].get(3, 0)}")
    print(f"  min/moy/max : {scenario_stats['min_size']} / {scenario_stats['avg_size']} / {scenario_stats['max_size']}")
    print()
    print("=== SIMILARITÉ INTERNE ===")
    print("Doublons exacts :", len(similarity["exact_dupes"]))
    print("Doublons normalisés :", len(similarity["normalized_dupes"]))
    print("Paires Jaccard >= 0.50 :", len(similarity["jaccard_pairs"]))
    if similarity["jaccard_pairs"]:
        for a, b, sim in similarity["jaccard_pairs"]:
            print(f"  {a} <-> {b} : {sim}")


if __name__ == "__main__":
    main()