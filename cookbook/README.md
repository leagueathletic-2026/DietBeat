# مطبخ DietBeat — كتاب وصفات الدايت

كتاب وصفات عربي (PDF للبيع) يضم ١٥٠ وصفة في ٨ أقسام، والقيم الغذائية لكل وصفة محسوبة من قاعدة بيانات **USDA FoodData Central (SR Legacy)**.

## طريقة البناء

```bash
pip install pyyaml jinja2
# مرة واحدة: نزّل بيانات USDA (ملكية عامة) وفك الضغط داخل cookbook/.usda/
curl -O https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip
unzip FoodData_Central_sr_legacy_food_csv_2018-04.zip -d .usda/

python3 scripts/usda.py build      # data/ingredient_map.yaml -> data/ingredients.json
python3 scripts/build.py --check   # راجع الأرقام والعلامات
python3 scripts/build.py           # -> output/book.html
node scripts/pdf.js                # -> output/DietBeat-Cookbook.pdf (يحتاج Playwright)
```

الملف `data/ingredients.json` موجود في المستودع، فلن تحتاج بيانات USDA إلا إذا أضفت مكوّنات جديدة.

## هيكل المشروع

| المسار | المحتوى |
|---|---|
| `recipes/NN-*.yaml` | الوصفات. كل ملف قسم واحد. |
| `data/ingredient_map.yaml` | ربط كل مكوّن برقم `fdc_id` في USDA وبالاسم العربي. |
| `data/ingredients.json` | قيم كل مكوّن لكل ١٠٠ جم، مُولَّدة من USDA. |
| `content/intro.yaml` | المقدمة والأدلة العلمية والمراجع وإخلاء المسؤولية. |
| `templates/` | تصميم الصفحات (HTML/CSS). |
| `images/<id>.jpg` | صور الوصفات (اختيارية). إذا وُجدت صورة تظهر تلقائياً في صفحة الوصفة. |

## كتابة وصفة

```yaml
- id: b05                 # فريد
  name: "اسم الوصفة"
  en: "English name"
  cuisine: "مصري"
  servings: 2
  time: 20                # دقائق
  ingredients:
    - [egg, 100, "٢ بيضة"]           # [المكوّن، الجرامات النيئة، الكمية بالعربي، اسم بديل اختياري]
    - [salt, 0, "حسب الرغبة"]        # ٠ جم = غير محسوب
  steps: ["...", "..."]
  tip: "..."              # اختياري
  swap: "..."             # اختياري: بدائل حسب الهدف
```

**العلامات تُحسب تلقائياً** من أرقام الحصة الواحدة (القواعد موجودة في `scripts/build.py` ومشروحة داخل الكتاب):

- **تخسيس:** حد أقصى للسعرات حسب نوع الطبق.
- **بروتين عالي:** ٣٠ جم أو أكثر، أو ١٥ جم بشرط أن يمثل ٣٠٪ أو أكثر من السعرات.
- **كيتو:** كربوهيدرات صافية ١٠ جم أو أقل.
- **غني بالألياف:** ٦ جم أو أكثر.
- **نباتي:** بدون لحوم أو دواجن أو أسماك.

سكربت `pdf.js` يتوقف بخطأ إذا كان محتوى أي صفحة أطول من صفحة A4.
