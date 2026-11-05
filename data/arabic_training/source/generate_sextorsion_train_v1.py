# -*- coding: utf-8 -*-
"""
generate_sextorsion_train_v1.py

Génère et valide :
data/arabic_training/source/sextorsion_train_candidates_v1.json

Lot d'entraînement MSA — label unique "Sextorsion".

Aucun appel à un modèle et aucun accès à AR-1 / AR-2.
"""

import json
import re
import unicodedata
from pathlib import Path
from collections import Counter, defaultdict

OUTPUT_PATH = Path("data/arabic_training/source/sextorsion_train_candidates_v1.json")

ENTRIES = [{'id': 'train_ar_sextorsion_0001',
  'text': 'يهددني بنشر صور حميمة تخصني إذا لم أرسل له المال الذي يطلبه.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0001'},
 {'id': 'train_ar_sextorsion_0002',
  'text': 'قال إنه سيرسل صوري الخاصة إلى عائلتي إن رفضت تنفيذ طلباته.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0002'},
 {'id': 'train_ar_sextorsion_0003',
  'text': 'يطلب مني مبالغ مالية مقابل أن يحتفظ بالمقطع الحميمي لنفسه ولا ينشره.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0001'},
 {'id': 'train_ar_sextorsion_0004',
  'text': 'هدد بنشر تسجيل خاص من مكالمة فيديو إذا لم أستجب لما يريده.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0003'},
 {'id': 'train_ar_sextorsion_0005',
  'text': 'يبتزني بصور خاصة ويشترط أن أدفع له حتى لا يرسلها إلى معارفي.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0004'},
 {'id': 'train_ar_sextorsion_0006',
  'text': 'يقول إنه سيكشف محتوى حميميًا يخصني إن توقفت عن الرد عليه.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0005'},
 {'id': 'train_ar_sextorsion_0007',
  'text': 'يطلب مني إرسال صور أخرى وإلا سينشر الصور الحميمة الموجودة لديه.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0006'},
 {'id': 'train_ar_sextorsion_0008',
  'text': 'هددني بإرسال مقطع خاص إلى زملائي إذا لم أحول له مبلغًا ماليًا.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0004'},
 {'id': 'train_ar_sextorsion_0009',
  'text': 'كلما حاولت قطع التواصل معه يذكرني بأنه يستطيع نشر صوري الحميمة في أي وقت إذا لم أطع طلباته.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0005'},
 {'id': 'train_ar_sextorsion_0010',
  'text': 'أجبرني على الاستمرار في الحديث معه لأنه يهدد بمشاركة محتوى خاص جدًا صوّرناه سابقًا.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0007'},
 {'id': 'train_ar_sextorsion_0011',
  'text': 'يطلب مني تحويل المال أسبوعيًا ويقول إن الصور الحميمة ستبقى سرية فقط ما دمت أدفع له.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0008'},
 {'id': 'train_ar_sextorsion_0012',
  'text': 'بعد أن حصل على صور خاصة مني بدأ يفرض شروطًا جديدة ويهدد بنشرها إذا رفضت أي شرط.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0009'},
 {'id': 'train_ar_sextorsion_0013',
  'text': 'أخبرني أن أمامي حتى نهاية اليوم لتنفيذ طلبه، وإلا فسيرسل المقطع الحميمي إلى أشخاص أعرفهم.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0010'},
 {'id': 'train_ar_sextorsion_0014',
  'text': 'يستخدم تسجيلًا خاصًا يحتفظ به للضغط علي حتى أستمر في تلبية طلباته رغم رفضي.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0007'},
 {'id': 'train_ar_sextorsion_0015',
  'text': 'قال بوضوح إن عدم دفع المبلغ يعني أن صوري الحميمة ستظهر على الإنترنت في اليوم نفسه.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0010'},
 {'id': 'train_ar_sextorsion_0016',
  'text': 'يهددني منذ أسابيع بمشاركة صور شخصية شديدة الخصوصية كلما حاولت إنهاء العلاقة أو الابتعاد عنه.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0011'},
 {'id': 'train_ar_sextorsion_0017',
  'text': 'في البداية كان يطلب مني أمورًا بسيطة، لكن بعد أن حصل على مقطع خاص أصبح يربط كل طلب جديد بتهديد صريح بنشره، ومع مرور الأيام '
          'ازدادت مطالبه وأصبح يكرر التهديد كلما حاولت رفض ما يريده أو تأجيله.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0009'},
 {'id': 'train_ar_sextorsion_0018',
  'text': 'بعد انتهاء علاقتنا احتفظ بصور حميمة لي، والآن يطالبني بالمال ويهدد بإرسالها إلى أقاربي إذا رفضت.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0012'},
 {'id': 'train_ar_sextorsion_0019',
  'text': 'أرسلت له صورة حميمة عندما كنت أثق به، ثم تغير أسلوبه بعد ذلك وبدأ يساومني عليها؛ طلب صورة أخرى أولًا ثم طلب المال، وفي كل مرة '
          'أرفض يقول إن ما لديه سيصل إلى أشخاص أعرفهم ولن يبقى خاصًا بيننا.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0006'},
 {'id': 'train_ar_sextorsion_0020',
  'text': 'منذ عدة أيام يرسل رسائل متكررة يقول فيها إن لديه محتوى حميميًا يمكنه إرساله إلى زملائي، ويستخدم هذا التهديد لإجباري على تنفيذ '
          'ما يطلبه كل مرة.',
  'label': 'Sextorsion',
  'style': 'direct',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0013'},
 {'id': 'train_ar_sextorsion_0021',
  'text': 'كلما رفضت طلبه يذكرني بالصور الخاصة التي يحتفظ بها.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0014'},
 {'id': 'train_ar_sextorsion_0022',
  'text': 'يذكّرني بأن عائلتي قد ترى صوري الخاصة إن رفضت طلباته.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0015'},
 {'id': 'train_ar_sextorsion_0023',
  'text': 'يلمّح إلى أن صورًا خاصة ستصل للآخرين إن لم أتعاون معه.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0016'},
 {'id': 'train_ar_sextorsion_0024',
  'text': 'منذ احتفظ بالمقطع الخاص أصبحت أخشى رفض طلباته.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0017'},
 {'id': 'train_ar_sextorsion_0025',
  'text': 'عندما أرفض الدفع يرسل لي لقطة من صورتي الخاصة.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0018'},
 {'id': 'train_ar_sextorsion_0026',
  'text': 'كل محاولة مني لقطع التواصل تقابل بتذكير هادئ بأن لديه صورًا حميمة لا أريد أن تصل إلى الآخرين.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0014'},
 {'id': 'train_ar_sextorsion_0027',
  'text': 'بعد الصور الحميمة صار يتعامل مع موافقتي كأنها مضمونة.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0017'},
 {'id': 'train_ar_sextorsion_0028',
  'text': 'يطلب مني أشياء لا أريدها، وكلما ترددت يلمح إلى أن المقطع الذي عنده قد لا يبقى سريًا.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0019'},
 {'id': 'train_ar_sextorsion_0029',
  'text': 'لم يقل صراحة إنه سينشر شيئًا، لكنه يكرر أن صوري ستظل آمنة طالما أفعل ما يطلبه.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0019'},
 {'id': 'train_ar_sextorsion_0030',
  'text': 'كل مرة أرفض فيها طلبًا جديدًا يسألني إن كنت مستعدة لأن يرى أقاربي المحتوى الذي يحتفظ به.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0015'},
 {'id': 'train_ar_sextorsion_0031',
  'text': 'أصبح المال شرطًا غير معلن لبقاء صوري الخاصة بعيدًا عن أعين الآخرين، فهو يطلبه كلما أراد التأكد من طاعتي.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0018'},
 {'id': 'train_ar_sextorsion_0032',
  'text': 'منذ أن حصل على التسجيل الخاص تغير أسلوبه تمامًا؛ صار يفرض علي قرارات لم أكن أوافق عليها، وكلما حاولت الاعتراض أعاد الحديث عن '
          'التسجيل وما قد يحدث لو وصل إلى الآخرين، ثم يضيف طلبًا جديدًا وكأن موافقتي لم تعد مهمة.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0020'},
 {'id': 'train_ar_sextorsion_0033',
  'text': 'لا أشعر أن موافقتي حقيقية عندما أرسل له ما يطلبه، لأنني أعرف أنه يحتفظ بمحتوى حميمي ويذكّرني به باستمرار.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0021'},
 {'id': 'train_ar_sextorsion_0034',
  'text': 'أحاول إنهاء التواصل، لكنه في كل مرة يعيد الحديث عن الصور التي لا أريد لأحد أن يراها، ثم يطلب مني شيئًا جديدًا.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0014'},
 {'id': 'train_ar_sextorsion_0035',
  'text': 'لم ينشر الصور حتى الآن، لكنه يجعل استمرار سريتها مرتبطًا دائمًا بما إذا كنت سأوافق على طلباته أم لا.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0019'},
 {'id': 'train_ar_sextorsion_0036',
  'text': 'كلما تأخرت في الرد يرسل رسالة قصيرة عن المقطع الخاص، ثم يضيف طلبًا جديدًا يريد تنفيذه في الحال.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0022'},
 {'id': 'train_ar_sextorsion_0037',
  'text': 'بعد خلاف بيننا بدأ يرسل تلميحات عن صور حميمة يحتفظ بها، ولم يكن يهدد بالنشر صراحة في البداية، لكنه كان يربط كل تلميح بطلب جديد، '
          'ومع تكرار الأمر فهمت أن خوفه الحقيقي بالنسبة لي هو وصول تلك الصور إلى أشخاص من محيطي.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0016'},
 {'id': 'train_ar_sextorsion_0038',
  'text': 'لا يطلب مني المال مباشرة في كل مرة، لكنه يذكرني بأن لديه صورًا خاصة ثم يرسل رقم الحساب الذي يريد التحويل إليه.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0023'},
 {'id': 'train_ar_sextorsion_0039',
  'text': 'منذ أسابيع وأنا أوافق على أشياء لا أريدها لأن الطرف الآخر يربط هدوء الوضع ببقاء محتوى خاص جدًا بعيدًا عن الناس.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0021'},
 {'id': 'train_ar_sextorsion_0040',
  'text': 'في البداية ظننت أن الأمر مجرد ضغط عاطفي بسبب خلاف بيننا، لكن مع مرور الوقت لاحظت أن كل مطالبه تعتمد على خوف واحد: أن يشارك '
          'تسجيلًا حميميًا احتفظ به من مكالمة سابقة، فهو يذكر التسجيل كلما توقفت عن الاستجابة ثم يطلب مني شيئًا جديدًا.',
  'label': 'Sextorsion',
  'style': 'indirect',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0020'},
 {'id': 'train_ar_sextorsion_0041',
  'text': 'بعد صورة حميمة على Instagram بدأ يطلب المال مقابل سريتها.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0024'},
 {'id': 'train_ar_sextorsion_0042',
  'text': 'سجّل مكالمة خاصة ويهدد بمشاركتها إن رفضت طلباته.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0025'},
 {'id': 'train_ar_sextorsion_0043',
  'text': 'شريكي السابق يضغط علي بصور حميمة كي أعود إليه.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0026'},
 {'id': 'train_ar_sextorsion_0044',
  'text': 'هدد بإرسال مقطع خاص لزملائي الجامعيين إن لم أدفع.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0027'},
 {'id': 'train_ar_sextorsion_0045',
  'text': 'تعرفت إلى شخص في لعبة عبر الإنترنت، وبعد أسابيع انتقل حديثنا إلى الرسائل الخاصة وأرسلت له صورًا حميمة لأنني وثقت به، لكنه بدأ '
          'لاحقًا يطلب مني شراء بطاقات رقمية له، ويقول في كل مرة إن الصور ستصل إلى لاعبين يعرفونني إذا لم أنفذ طلبه.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0028'},
 {'id': 'train_ar_sextorsion_0046',
  'text': 'كان بيننا تواصل شخصي على WhatsApp، وبعد خلاف بسيط صار يهدد بإرسال صور خاصة إلى أفراد أسرتي إذا لم أستمر في الحديث معه.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0029'},
 {'id': 'train_ar_sextorsion_0047',
  'text': 'أرسل لي شخص على Telegram لقطة من مقطع خاص يملكه، ثم طلب تحويلًا ماليًا خلال ساعات وإلا سيرسله إلى زملاء العمل.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0030'},
 {'id': 'train_ar_sextorsion_0048',
  'text': 'بعد أن وثقت به على تطبيق تعارف وأرسلت له صورة حميمة، أنشأ حسابًا آخر وبدأ يطلب المزيد من الصور مقابل إبقاء الأولى سرية.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0031'},
 {'id': 'train_ar_sextorsion_0049',
  'text': 'اكتشفت أن شريكي السابق احتفظ بتسجيل حميمي من فترة علاقتنا، وهو الآن يربط عدم نشره بموافقتي على مقابلته من جديد.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0032'},
 {'id': 'train_ar_sextorsion_0050',
  'text': 'في محادثة خاصة على Messenger، قال إن لديه نسخة من صور شديدة الخصوصية وطلب مني دفع مبلغ قبل نهاية الأسبوع حتى لا تصل إلى أقاربي.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0033'},
 {'id': 'train_ar_sextorsion_0051',
  'text': 'بدأ الأمر برسائل عادية عبر TikTok ثم انتقلنا إلى مكالمة فيديو خاصة، وبعد أيام أخبرني أنه سجّل جزءًا من المكالمة دون علمي، ومنذ '
          'ذلك الوقت صار يحدد مبالغ مالية يريدها ويهدد بأن التسجيل سيصل إلى متابعيني إذا تجاهلت طلباته أو توقفت عن الرد.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0034'},
 {'id': 'train_ar_sextorsion_0052',
  'text': 'في حساب مجهول على منصة اجتماعية، أرسل لي شخص نسخة مصغرة من صورة حميمة تخصني ثم طالبني بخدمة معينة مقابل ألا ينشر النسخة '
          'الكاملة.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0035'},
 {'id': 'train_ar_sextorsion_0053',
  'text': 'أثناء علاقة سابقة كنا نتبادل محتوى حميميًا باختيارنا، وبعد الانفصال طلب مني الطرف الآخر أن أعود إليه، وعندما رفضت بدأ يذكر '
          'الصور التي ما زالت لديه ويقول إنها قد تصل إلى أصدقائي، ثم كرر هذا الضغط كلما أكدت أنني لا أريد استئناف العلاقة.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0036'},
 {'id': 'train_ar_sextorsion_0054',
  'text': 'في مجموعة عمل مغلقة يعرف فيها الجميع بعضهم، هدد شخص بإرسال صورة شديدة الخصوصية لي إلى أعضاء المجموعة إذا لم أوافق على ما يطلبه.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0037'},
 {'id': 'train_ar_sextorsion_0055',
  'text': 'تواصل معي حساب لا أعرفه وادعى أنه حصل على مقطع حميمي من هاتفي، ولم أصدقه في البداية، ثم أرسل لقطة واضحة تثبت امتلاكه للمقطع '
          'وطالبني بتحويل مبلغ مالي خلال يوم واحد، وقال إن عدم الدفع سيعني إرساله إلى أشخاص موجودين في قائمة معارفي.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0038'},
 {'id': 'train_ar_sextorsion_0056',
  'text': 'بعد محادثات خاصة استمرت أشهرًا، بدأ الشخص الآخر يرسل تهديدات متكررة بأنه سيشارك الصور الحميمة مع أصدقائي كلما حاولت التوقف عن '
          'التواصل.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0039'},
 {'id': 'train_ar_sextorsion_0057',
  'text': 'خلال علاقة عن بعد أرسلت صورًا خاصة بمحض إرادتي، لكن الطرف الآخر صار يستخدمها الآن لإجباري على تحويل مبالغ صغيرة بصورة متكررة.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0040'},
 {'id': 'train_ar_sextorsion_0058',
  'text': 'في حسابي على Facebook وصلتني رسالة من شخص يحتفظ بصورة حميمة لي، ويطلب مني إعطاءه كلمة مرور حساب آخر مقابل عدم مشاركتها.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0041'},
 {'id': 'train_ar_sextorsion_0059',
  'text': 'تحدث معي شخص لأسابيع وهو ينتحل صفة صديق أعرفه، وبعد أن وثقت به أرسلت له صورة خاصة، ثم كشف لاحقًا أنه شخص آخر وبدأ يطالبني '
          'بالمال، ويكرر أن الصورة ستصل إلى أفراد عائلتي إذا رفضت التحويل أو حاولت إنهاء التواصل معه.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0042'},
 {'id': 'train_ar_sextorsion_0060',
  'text': 'بدأت المشكلة في تطبيق تعارف ثم امتدت إلى أكثر من منصة؛ الشخص نفسه يلاحقني برسائل فيها صور خاصة لي ويحدد في كل مرة طلبًا جديدًا '
          'يجب تنفيذه حتى لا يرسلها إلى أشخاص أعرفهم.',
  'label': 'Sextorsion',
  'style': 'contextual',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0043'},
 {'id': 'train_ar_sextorsion_0061',
  'text': 'أصبح محتوى حميمي يخصني وسيلة ضغط يستخدمها شخص لإجباري على تنفيذ ما يريده.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0044'},
 {'id': 'train_ar_sextorsion_0062',
  'text': 'يربط بقاء صوري الخاصة سرية بموافقتي على طلباته المتكررة.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0045'},
 {'id': 'train_ar_sextorsion_0063',
  'text': 'يستعمل تسجيلًا شخصيًا حساسًا كورقة ضغط كلما رفضت ما يطلبه.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0046'},
 {'id': 'train_ar_sextorsion_0064',
  'text': 'تحولت الصور التي وثقت به وأرسلتها له إلى أداة يساومني بها الآن.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0047'},
 {'id': 'train_ar_sextorsion_0065',
  'text': 'كل طلب جديد مرتبط بتهديده بكشف المحتوى الخاص الذي يملكه.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0048'},
 {'id': 'train_ar_sextorsion_0066',
  'text': 'يضعني أمام خيارين باستمرار: أن أوافق على طلبه أو أخاطر بأن يرى الآخرون صورًا حميمة تخصني.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0049'},
 {'id': 'train_ar_sextorsion_0067',
  'text': 'أشعر أن الطرف الآخر حول خصوصيتي إلى وسيلة تحكم، فهو يذكر المحتوى الحميمي كلما أراد مني مالًا أو استجابة معينة.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0050'},
 {'id': 'train_ar_sextorsion_0068',
  'text': 'المشكلة ليست مجرد امتلاكه للصور، بل أنه يجعل عدم نشرها مشروطًا بأن أنفذ ما يطلبه مرة بعد أخرى.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0051'},
 {'id': 'train_ar_sextorsion_0069',
  'text': 'يستخدم الخوف من كشف تسجيل خاص لإبقائي تحت ضغط مستمر، وكلما ظننت أن الأمر انتهى يظهر مطلب جديد.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0052'},
 {'id': 'train_ar_sextorsion_0070',
  'text': 'أصبحت سرية محتوى شخصي حساس بالنسبة لي مرتبطة عمليًا برضوخي لما يريده هذا الشخص.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0053'},
 {'id': 'train_ar_sextorsion_0071',
  'text': 'كلما حاولت وضع حدود جديدة في التواصل معه يعيد فتح موضوع الصور الحميمة التي يحتفظ بها، ثم يلمح إلى أن بقاءها سرية يعتمد على مدى '
          'تعاوني، وبعد ذلك يضيف طلبًا آخر لا أريده، فأشعر أن كل محاولة لاستعادة قراري تؤدي إلى جولة جديدة من الضغط.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0054'},
 {'id': 'train_ar_sextorsion_0072',
  'text': 'يشعرني بأن التحكم في مصير صوري الخاصة بيده وحده، ويستغل ذلك ليفرض علي أمورًا لم أوافق عليها.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0055'},
 {'id': 'train_ar_sextorsion_0073',
  'text': 'الضغط يتكرر بالشكل نفسه: يذكرني بالمقطع الخاص، يحدد ما يريد، ثم يلمح إلى أن الرفض ستكون له عواقب علنية.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0056'},
 {'id': 'train_ar_sextorsion_0074',
  'text': 'المحتوى الذي كان من المفترض أن يبقى بيننا تحول إلى أساس لمساومة مستمرة؛ أحيانًا يطلب المال وأحيانًا يطلب قرارات شخصية لا '
          'أريدها، وفي كل مرة يربط موافقتي ببقاء ذلك المحتوى بعيدًا عن الآخرين، لذلك لم تعد المسألة مجرد خلاف بل ضغط متكرر باستخدام '
          'الخصوصية.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0057'},
 {'id': 'train_ar_sextorsion_0075',
  'text': 'ما يقلقني هو أن الشخص لا يهدد مرة واحدة فقط؛ بل يعيد استخدام الصور الحميمة كلما أراد زيادة مطالبه أو تغيير شروطه.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0058'},
 {'id': 'train_ar_sextorsion_0076',
  'text': 'أدركت أنني لم أعد أتصرف بحرية، لأن أي رفض مني يقابله فورًا بتذكير بأن لديه مادة خاصة يمكنه كشفها للآخرين.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0059'},
 {'id': 'train_ar_sextorsion_0077',
  'text': 'يعامل المحتوى الحميمي كأنه ضمان يجبرني على الاستمرار في الدفع؛ كلما أرسلت مبلغًا ظننت أن الأمر انتهى، لكنه يعود بعد أيام بمبلغ '
          'جديد ويذكرني بأن الصور ما زالت لديه، ثم يعيد التهديد نفسه إذا قلت إنني لن أرسل أي مال إضافي.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0060'},
 {'id': 'train_ar_sextorsion_0078',
  'text': 'منذ أن حصل على التسجيل الخاص، أصبح يحدد مهلًا زمنية لتنفيذ مطالبه ثم يربط انتهاء المهلة بإرسال التسجيل إلى أشخاص من محيطي.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0061'},
 {'id': 'train_ar_sextorsion_0079',
  'text': 'في كل مرة أحاول استعادة السيطرة على قراراتي يعيد الشخص استخدام المحتوى الخاص نفسه ليفرض شرطًا جديدًا؛ بدأ بطلب واحد ثم أضاف '
          'طلبات مالية وشخصية أخرى، ومع كل رفض يذكر ما يمكن أن يفعله بالصور، حتى أصبحت المطالب تتوسع بدل أن تنتهي.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0062'},
 {'id': 'train_ar_sextorsion_0080',
  'text': 'بدأ الأمر بطلب واحد ظننته سينهي المشكلة، لكن بعد أن نفذته عاد الشخص بمطلب آخر ثم ثالث، وفي كل مرة يستخدم الصور الحميمة نفسها '
          'ويهدد بأنها ستصل إلى أشخاص أعرفهم إذا توقفت عن الاستجابة.',
  'label': 'Sextorsion',
  'style': 'paraphrase',
  'boundary_with': None,
  'scenario_group': 'sextorsion_scenario_0063'},
 {'id': 'train_ar_sextorsion_0081',
  'text': 'الصور الحميمة لم تُنشر حتى الآن، لكنه يهدد بنشرها إذا لم أدفع له.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': "Diffusion non consentie d'images",
  'scenario_group': 'sextorsion_scenario_0064'},
 {'id': 'train_ar_sextorsion_0082',
  'text': 'يحتفظ بمقطع خاص ويهدد بمشاركته إن رفضت طلبه.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': "Diffusion non consentie d'images",
  'scenario_group': 'sextorsion_scenario_0065'},
 {'id': 'train_ar_sextorsion_0083',
  'text': 'أرسل لي صورة مصغرة من المحتوى ليؤكد أنه يملكه، لكنه لم ينشره بعد ويشترط المال حتى يبقى غير منشور.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': "Diffusion non consentie d'images",
  'scenario_group': 'sextorsion_scenario_0064'},
 {'id': 'train_ar_sextorsion_0084',
  'text': 'كل ما أخشاه هو التهديد المستمر بإرسال الصور إلى الآخرين إذا لم أستجب؛ حتى هذه اللحظة لم يرسلها لأي شخص بحسب ما أعلم.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': "Diffusion non consentie d'images",
  'scenario_group': 'sextorsion_scenario_0065'},
 {'id': 'train_ar_sextorsion_0085',
  'text': 'ما زالت الصور خارج العلن، لكن الشخص حدد لي مهلة وقال إن انتهاءها دون تنفيذ طلبه يعني أنه سيضعها على الإنترنت.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': "Diffusion non consentie d'images",
  'scenario_group': 'sextorsion_scenario_0066'},
 {'id': 'train_ar_sextorsion_0086',
  'text': 'أوضح لي أنه لم يشارك التسجيل مع أحد حتى الآن، ثم أعطاني حتى مساء الغد لتحويل المال مقابل استمرار سريته.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': "Diffusion non consentie d'images",
  'scenario_group': 'sextorsion_scenario_0066'},
 {'id': 'train_ar_sextorsion_0087',
  'text': 'حتى الآن لا يوجد نشر فعلي للمحتوى الحميمي، وهذا ما يجعلني أميز بين ما يحدث وبين نشر الصور نفسه، لكن الشخص يكرر التهديد '
          'بالمشاركة مع كل طلب جديد، ويقول إن بقاء المحتوى بعيدًا عن الناس يعتمد على استجابتي، لذلك أشعر أنني مضطرة للرضوخ حتى لا ينفذ '
          'تهديده.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': "Diffusion non consentie d'images",
  'scenario_group': 'sextorsion_scenario_0067'},
 {'id': 'train_ar_sextorsion_0088',
  'text': 'يهدد بنشر صور حميمة إن لم أدفع، وأفكر في الإبلاغ.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': 'Signalement',
  'scenario_group': 'sextorsion_scenario_0068'},
 {'id': 'train_ar_sextorsion_0089',
  'text': 'ما زال يطالبني بالمال مقابل عدم إرسال المقطع الخاص، وقد فكرت في اتخاذ إجراء رسمي إذا استمر في الضغط علي.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': 'Signalement',
  'scenario_group': 'sextorsion_scenario_0068'},
 {'id': 'train_ar_sextorsion_0090',
  'text': 'كل مرة أرفض طلبه يعود للحديث عن الصور الحميمة التي يحتفظ بها ويقول إنها قد تصل إلى أشخاص أعرفهم، ولذلك بدأت أفكر جديًا في إبلاغ '
          'جهة مختصة، لكن هذه الفكرة جاءت بعد أسابيع من الضغط؛ المشكلة الأساسية ما زالت أنه يستخدم المحتوى الخاص لإجباري على الاستجابة لما '
          'يريده.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': 'Signalement',
  'scenario_group': 'sextorsion_scenario_0069'},
 {'id': 'train_ar_sextorsion_0091',
  'text': 'منذ أسبوعين يربط عدم نشر تسجيل خاص بتنفيذ مطالبه، وبعد تكرار التهديدات مرات عديدة أصبحت أفكر في خطوة رسمية، من دون أن يتغير '
          'جوهر المشكلة وهو استخدام التسجيل لإجباري على الاستجابة.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': 'Signalement',
  'scenario_group': 'sextorsion_scenario_0069'},
 {'id': 'train_ar_sextorsion_0092',
  'text': 'تهديده بنشر الصور الحميمة يسبب لي خوفًا شديدًا، لكنه لم يهددني بأي أذى جسدي مباشر.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': "Situation d'urgence",
  'scenario_group': 'sextorsion_scenario_0070'},
 {'id': 'train_ar_sextorsion_0093',
  'text': 'أشعر بقلق كبير بسبب تهديداته المتكررة بالمحتوى الخاص، لكن لا توجد أي إشارة إلى خطر جسدي وشيك حاليًا.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': "Situation d'urgence",
  'scenario_group': 'sextorsion_scenario_0070'},
 {'id': 'train_ar_sextorsion_0094',
  'text': 'الضغط النفسي شديد لأن الشخص يلوح بنشر مقطع حميمي إذا لم أنفذ طلباته، ومع ذلك فالوضع حتى الآن يقتصر على الابتزاز الرقمي ولا يوجد '
          'تهديد فوري لسلامتي الجسدية.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': "Situation d'urgence",
  'scenario_group': 'sextorsion_scenario_0071'},
 {'id': 'train_ar_sextorsion_0095',
  'text': 'أحتفظ الآن بلقطات شاشة لرسائله التي يطالب فيها بالمال مقابل عدم نشر الصور الحميمة.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': 'Conservation des preuves',
  'scenario_group': 'sextorsion_scenario_0072'},
 {'id': 'train_ar_sextorsion_0096',
  'text': 'بدأت أوثق كل تهديد يرسله، لكن المشكلة الأساسية أنه ما زال يستخدم المقطع الخاص لإجباري على تنفيذ طلباته.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': 'Conservation des preuves',
  'scenario_group': 'sextorsion_scenario_0072'},
 {'id': 'train_ar_sextorsion_0097',
  'text': 'منذ أن بدأ يطالبني بتحويل المال مقابل بقاء الصور الحميمة سرية، صرت أحفظ الرسائل والتواريخ واللقطات التي يظهر فيها التهديد، ليس '
          'لأن التوثيق هو مشكلتي الأساسية، بل لأن الشخص ما زال يكرر المطالب ويربط كل مرة عدم نشر المحتوى باستمرار الدفع أو تنفيذ ما يريده.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': 'Conservation des preuves',
  'scenario_group': 'sextorsion_scenario_0073'},
 {'id': 'train_ar_sextorsion_0098',
  'text': 'يهددني بنشر صور حميمة إذا رفضت دفع المال، وأتساءل أحيانًا كيف ينظر القانون إلى هذا النوع من الضغط.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': 'Informations juridiques',
  'scenario_group': 'sextorsion_scenario_0074'},
 {'id': 'train_ar_sextorsion_0099',
  'text': 'ما زال يستخدم التسجيل الخاص لفرض مطالبه علي، وبدأت أفكر فيما إذا كانت هذه الأفعال لها تبعات قانونية.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': 'Informations juridiques',
  'scenario_group': 'sextorsion_scenario_0074'},
 {'id': 'train_ar_sextorsion_0100',
  'text': 'منذ أسابيع يربط بقاء محتوى حميمي سريًا بتنفيذي لما يطلبه، وأتساءل عن الوضع القانوني لهذا السلوك، لكن التهديد المشروط بالمحتوى '
          'يظل جوهر ما أتعرض له.',
  'label': 'Sextorsion',
  'style': 'boundary',
  'boundary_with': 'Informations juridiques',
  'scenario_group': 'sextorsion_scenario_0075'}]

EXPECTED_STYLES = {
    "direct": 20,
    "indirect": 20,
    "contextual": 20,
    "paraphrase": 20,
    "boundary": 20,
}

EXPECTED_BOUNDARIES = {
    "Diffusion non consentie d'images": 7,
    "Signalement": 4,
    "Situation d'urgence": 3,
    "Conservation des preuves": 3,
    "Informations juridiques": 3,
}

VALID_BOUNDARY_INTENTS = {
    "Cyberharcèlement",
    "Sextorsion",
    "Piratage de compte",
    "Divulgation de données personnelles (Doxing)",
    "Conservation des preuves",
    "Informations juridiques",
    "Usurpation d'identité",
    "Diffusion non consentie d'images",
    "Signalement",
    "Situation d'urgence",
    "Accompagnement de la victime",
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
    return len(a & b) / len(a | b) if (a | b) else 0.0

def word_count(text: str) -> int:
    return len(text.split())

def validate_structure(entries: list[dict]) -> None:
    assert len(entries) == 100, f"Attendu 100 exemples, obtenu {len(entries)}"

    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)) == 100, "IDs non uniques"
    assert all(e["label"] == "Sextorsion" for e in entries), "Label incorrect détecté"

    expected_fields = {"id", "text", "label", "style", "boundary_with", "scenario_group"}
    for e in entries:
        assert set(e.keys()) == expected_fields, f"Champs inattendus : {e['id']}"
        assert e["scenario_group"], f"scenario_group vide : {e['id']}"
        if e["boundary_with"] is not None:
            assert e["boundary_with"] in VALID_BOUNDARY_INTENTS, (
                f"boundary_with invalide : {e['id']} -> {e['boundary_with']}"
            )

    style_counts = Counter(e["style"] for e in entries)
    assert style_counts == Counter(EXPECTED_STYLES), f"Styles incorrects : {style_counts}"

    boundary_counts = Counter(
        e["boundary_with"] for e in entries if e["style"] == "boundary"
    )
    assert boundary_counts == Counter(EXPECTED_BOUNDARIES), (
        f"Boundary incorrect : {boundary_counts}"
    )

    assert all(
        e["boundary_with"] is None
        for e in entries
        if e["style"] != "boundary"
    ), "boundary_with non-null hors style boundary"

def similarity_stats(entries: list[dict], threshold: float = 0.50) -> dict:
    exact, normalized, jaccard = [], [], []
    seen_exact, seen_norm = {}, {}

    norms = {e["id"]: normalize_arabic_text(e["text"]) for e in entries}
    toks = {e["id"]: tokenize(e["text"]) for e in entries}

    for e in entries:
        text = e["text"]
        if text in seen_exact:
            exact.append((seen_exact[text], e["id"]))
        else:
            seen_exact[text] = e["id"]

        norm = norms[e["id"]]
        if norm in seen_norm:
            normalized.append((seen_norm[norm], e["id"]))
        else:
            seen_norm[norm] = e["id"]

    ids = [e["id"] for e in entries]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            sim = jaccard_similarity(toks[ids[i]], toks[ids[j]])
            if sim >= threshold:
                jaccard.append((ids[i], ids[j], round(sim, 3)))

    return {"exact": exact, "normalized": normalized, "jaccard": jaccard}

def scenario_stats(entries: list[dict]) -> dict:
    groups = defaultdict(list)
    for e in entries:
        groups[e["scenario_group"]].append(e["id"])

    sizes = [len(v) for v in groups.values()]
    dist = Counter(sizes)

    return {
        "unique": len(groups),
        "size_1": dist.get(1, 0),
        "size_2": dist.get(2, 0),
        "size_3": dist.get(3, 0),
        "min": min(sizes),
        "avg": round(sum(sizes) / len(sizes), 2),
        "max": max(sizes),
    }

def length_stats(entries: list[dict]) -> dict:
    return {
        "short": sum(word_count(e["text"]) < 15 for e in entries),
        "medium": sum(15 <= word_count(e["text"]) <= 30 for e in entries),
        "long": sum(word_count(e["text"]) > 30 for e in entries),
    }

def main() -> None:
    validate_structure(ENTRIES)
    sim = similarity_stats(ENTRIES)
    scen = scenario_stats(ENTRIES)
    leng = length_stats(ENTRIES)

    assert scen["max"] <= 3, f"scenario_group > 3 détecté : {scen['max']}"

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(ENTRIES, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Fichier écrit : {OUTPUT_PATH}")
    print(f"Total : {len(ENTRIES)}")
    print()
    print("=== STYLES ===")
    for k, v in Counter(e["style"] for e in ENTRIES).items():
        print(f"  {k:<12} : {v}")
    print()
    print("=== BOUNDARY_WITH ===")
    for k, v in Counter(e["boundary_with"] for e in ENTRIES if e["style"] == "boundary").items():
        print(f"  {k} : {v}")
    print()
    print("=== LONGUEUR ===")
    print(f"  courtes (<15 mots) : {leng['short']}")
    print(f"  moyennes (15-30)   : {leng['medium']}")
    print(f"  longues (>30)      : {leng['long']}")
    print()
    print("=== SCENARIO_GROUP ===")
    print(f"  groupes uniques : {scen['unique']}")
    print(f"  taille 1 : {scen['size_1']}")
    print(f"  taille 2 : {scen['size_2']}")
    print(f"  taille 3 : {scen['size_3']}")
    print(f"  min/moy/max : {scen['min']} / {scen['avg']} / {scen['max']}")
    print()
    print("=== SIMILARITÉ INTERNE ===")
    print("Doublons exacts :", len(sim["exact"]))
    print("Doublons normalisés :", len(sim["normalized"]))
    print("Paires Jaccard >= 0.50 :", len(sim["jaccard"]))
    if sim["jaccard"]:
        for a, b, score in sim["jaccard"]:
            print(f"  {a} <-> {b} : {score}")

if __name__ == "__main__":
    main()