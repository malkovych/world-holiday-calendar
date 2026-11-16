"""Generate the World Holiday Calendar UTF-8 CSV snapshot. Requires holidays==0.108."""
import csv, re, hashlib, warnings, unicodedata
from pathlib import Path
from datetime import date, timedelta
from dateutil.easter import easter, EASTER_ORTHODOX
import holidays

out = Path.cwd()
if holidays.__version__ != '0.108':
    raise SystemExit('Install holidays==0.108 before generating the 2026–2028 snapshot.')
years=[2026,2027,2028]
UN='https://www.un.org/en/observances/list-days-weeks'
UA='https://ukc.gov.ua/knowdledge/svyatkovi-ta-nerobochi-dni/'
UA2='https://uinp.gov.ua/'
PKG='https://holidays.readthedocs.io/en/latest/'
FAITH='https://www.davidson.edu/offices-and-services/religious-and-spiritual-life/observance-calendar'
MUSIC='https://www.culture.gouv.fr/evenements-nationaux/fete-de-la-musique'
PKG_SOURCE={'PL':'https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20250000296/O/D20250296.pdf'}
defs=[]
occ=[]
cols=['occurrence_id','event_id','start_date','end_date','market','category','title_uk','title_en_or_local','date_status','campaign_policy','prepare_days_before','send_days_before','send_local_time','timezone_policy','music_brief_uk','source_url','notes']
def slug(label):
    t=unicodedata.normalize('NFKD',label).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+','-',t).strip('-')[:65] or 'holiday'
def nth(y,m,w,n):
    first=date(y,m,1)
    return first+timedelta(days=(w-first.weekday())%7+(n-1)*7)
def expand(rule,y):
    if rule.startswith('D:'):
        return [date.fromisoformat(s) for s in rule[2:].split(',') if int(s[:4])==y]
    if rule.startswith('W:'):
        return [nth(y,*map(int,rule[2:].split(':')))]
    if rule.startswith(('E:','O:','T:')):
        base={'E':easter(y),'O':easter(y,EASTER_ORTHODOX),'T':nth(y,11,3,4)}[rule[0]]
        return [base+timedelta(days=int(rule[2:]))]
    if rule.startswith('N:'):
        return [date(y,1,1)+timedelta(days=int(rule[2:])-1)]
    if rule.startswith('L:'):
        month,weekday=map(int,rule[2:].split(':'))
        last=date(y,month+1,1)-timedelta(days=1)
        return [last-timedelta(days=(last.weekday()-weekday)%7)]
    if rule.startswith('V:'):
        day=date.fromisoformat(f'{y}-{rule[2:]}')
        return [day-timedelta(days=day.weekday() or 7)]
    if rule.startswith('K:'):
        day=date.fromisoformat(f'{y}-{rule[2:]}')
        return [day-timedelta(days=day.weekday()==6)]
    return [date.fromisoformat(f'{y}-{rule}')]
def add_occ(event,day,end,market,category,uk,en,status,policy,prepare,send,brief,source,notes):
    occ.append([f'{event}:{market}:{day}',event,day.isoformat(),end.isoformat(),market,category,uk,en,status,policy,prepare,send,'10:00' if send!='' else '', 'recipient_iana',brief,source,notes])
def add_def(event,rule,uk,en,markets='WORLD',category='culture',policy='targeted',source='',notes='',status=None,length=1):
    targets=markets.split(',')
    prepare=14 if category in {'retail','faith'} else 7
    send=3 if category in {'retail','faith','family','personal'} else 0
    mood={
      'faith':'Акустичні або інструментальні теми. Підібрати звучання для конкретної традиції.',
      'retail':'Енергійний інструментальний трек для короткого промо.',
      'family':'Тепла акустика, мʼякий ритм і мелодія, придатна для персонального привітання.',
      'personal':'Персональний музичний подарунок за вказаним приводом і жанром.',
      'music':'Інструментальний трек у жанрі, повʼязаному з подією.',
      'memorial':'Стримана інструментальна композиція за редакційним погодженням.',
      'civic':'Інструментальна композиція з урахуванням місцевого контексту.',
    }
    distinct={
      'valentine':'Інтимна акустична балада або мʼякий соул для персонального присвячення.',
      'halloween':'Ігровий містичний саундтрек із піцикато та мʼякими дисонансами.',
      'new-year':'Святковий поп або диско з наростанням до опівночі.',
      'jazz-day':'Свінг або джазове тріо з імпровізацією.',
      'ua-independence':'Сучасний український фольк з акустичними інструментами.',
      'child-birth':'Мʼяка колискова з делікатним фортепіано.',
    }
    brief=distinct.get(event,mood.get(category,'Інструментальна композиція на тему події.')) if policy!='off' else ''
    if policy=='review':
        brief='Редакційна перевірка. '+brief
    if policy=='off':
        prepare=send=''
    if not notes:
        if category=='statutory_ua':
            notes='Календарна дата зі ст. 73. Застосування режиму неробочих днів залежить від чинних норм, зокрема воєнного стану.'
        elif rule=='USER':
            notes='Дату й щорічний або одноразовий повтор задає користувач або застосунок. Для 29 лютого застосувати налаштування користувача.'
        elif category=='un':
            notes='Міжнародна дата. Для кампанії потрібна тематично релевантна аудиторія.'
    source=source or {'un':UN,'statutory_ua':UA}.get(category,'')
    if not source and markets=='UA' and rule!='USER':
        source=UA2
    status=status or ('provider_estimate' if rule.startswith('D:') else 'rule')
    defs.append([event,rule,markets,category,uk,en,policy,prepare,send,brief,source,notes])
    if rule=='USER':
        return
    for year in years:
        for day in expand(rule,year):
            for market in targets:
                add_occ(event,day,day+timedelta(days=length-1),market,category,uk,en,status,policy,prepare,send,brief,source,notes)

for line in "new-year|01-01|Новий рік|New Year's Day\nnew-years-eve|12-31|Переддень Нового року|New Year's Eve\nvalentine|02-14|День святого Валентина|Valentine's Day\nhalloween|10-31|Гелловін|Halloween\napril-fools|04-01|День сміху|April Fools' Day\nst-patrick|03-17|День святого Патрика|Saint Patrick's Day|IE,US,CA,GB,AU\ncinco-de-mayo|05-05|Сінко-де-Майо|Cinco de Mayo|MX,US\nbastille|07-14|Національне свято Франції|Bastille Day|FR\nday-of-dead|11-02|День мертвих|Día de Muertos|MX|culture|review\nkings-day|K:04-27|День короля|King's Day|NL|culture|review\neurope-day|05-09|День Європи|Europe Day|EU,UA\nchristmas-eve|12-24|Святвечір|Christmas Eve|WORLD|faith|targeted\nchristmas|12-25|Різдво|Christmas Day|WORLD|faith|targeted\northodox-nativity-old|01-07|Різдво за юліанським календарем|Nativity on the Julian calendar|WORLD|faith|targeted\nepiphany|01-06|Богоявлення|Epiphany|WORLD|faith|targeted\nst-nicholas|12-06|День святого Миколая|Saint Nicholas Day|UA,PL,NL,DE,AT,BE|faith|targeted\nwestern-easter|E:0|Великдень за західною пасхалією|Western Easter|WORLD|faith|targeted\northodox-easter|O:0|Великдень за східною пасхалією|Orthodox Easter|WORLD|faith|targeted\ngood-friday|E:-2|Страсна пʼятниця за західною пасхалією|Western Good Friday|WORLD|faith|review\neaster-monday|E:1|Великодній понеділок|Western Easter Monday|WORLD|faith|targeted\nash-wednesday|E:-46|Попільна середа|Ash Wednesday|WORLD|faith|review\nmardi-gras|E:-47|Марді Гра|Mardi Gras|WORLD|culture|targeted\npalm-sunday|E:-7|Вербна неділя за західною пасхалією|Western Palm Sunday|WORLD|faith|targeted\npalm-sunday-east|O:-7|Вербна неділя за східною пасхалією|Orthodox Palm Sunday|WORLD|faith|targeted\npentecost|E:49|Пʼятидесятниця за західною пасхалією|Western Pentecost|WORLD|faith|targeted\ntrinity-east|O:49|Трійця за східною пасхалією|Orthodox Pentecost|WORLD|faith|targeted\ncorpus-christi|E:60|Свято Тіла і Крові Христових|Corpus Christi|PL,AT,BR,CO,HR,PT|faith|targeted\nall-saints|11-01|День усіх святих|All Saints' Day|WORLD|faith|review\nboxing-day|12-26|Boxing Day|Boxing Day|GB,CA,AU,NZ|retail|targeted\nmothers-ua-us|W:05:6:2|День матері|Mother's Day|UA,US,CA,AU,DE,NZ|family|targeted\nmothers-pl|05-26|День матері в Польщі|Mother's Day in Poland|PL|family|targeted\nmothers-gb|E:-21|Материнська неділя|Mothering Sunday|GB,IE|family|targeted\nmothers-mx|05-10|День матері в Мексиці|Mother's Day in Mexico|MX|family|targeted\nfathers-ua-us|W:06:6:3|День батька|Father's Day|UA,US,CA,GB,IE|family|targeted\nfathers-pl|06-23|День батька в Польщі|Father's Day in Poland|PL|family|targeted\nfathers-au|W:09:6:1|День батька в Австралії та Новій Зеландії|Father's Day in Australia and New Zealand|AU,NZ|family|targeted\nchildren-pl|06-01|День дитини в Польщі|Children's Day in Poland|PL|family|targeted\ngrandmother-pl|01-21|День бабусі в Польщі|Grandmother's Day in Poland|PL|family|targeted\ngrandfather-pl|01-22|День дідуся в Польщі|Grandfather's Day in Poland|PL|family|targeted\nwomens-day|03-08|Міжнародний жіночий день|International Women's Day|WORLD|un|review\nthanksgiving-us|W:11:3:4|День подяки в США|Thanksgiving in the United States|US|family|targeted\nthanksgiving-ca|W:10:0:2|День подяки в Канаді|Thanksgiving in Canada|CA|family|targeted\nblack-friday|T:1|Чорна пʼятниця|Black Friday|WORLD|retail|targeted\nsmall-business-saturday|T:2|Субота малого бізнесу|Small Business Saturday|US|retail|targeted\ncyber-monday|T:4|Кіберпонеділок|Cyber Monday|WORLD|retail|targeted\ngiving-tuesday|T:5|Щедрий вівторок|GivingTuesday|WORLD|community|targeted\nsingles-day|11-11|День самотніх / 11.11|Singles' Day|CN|retail|targeted\nmusic-day-june|06-21|Свято музики|Fête de la musique|WORLD|music|targeted\nmusic-day-oct|10-01|Міжнародний день музики|International Music Day|WORLD|music|review\njazz-day|04-30|Міжнародний день джазу|International Jazz Day|WORLD|un|targeted\ndance-day|04-29|Міжнародний день танцю|International Dance Day|WORLD|arts|targeted\ntheatre-day|03-27|Всесвітній день театру|World Theatre Day|WORLD|arts|targeted\npi-day|03-14|День числа пі|Pi Day|WORLD|culture|targeted\nstar-wars|05-04|День «Зоряних війн»|Star Wars Day|WORLD|culture|review\npride-june|06-01|Початок місяця Pride|Pride Month begins|US,CA,GB|community|targeted\nteachers-ua|W:10:6:1|День працівників освіти|Education Workers' Day in Ukraine|UA|career|targeted\nteachers-pl|10-14|День національної освіти Польщі|National Education Day in Poland|PL|career|targeted\ntlusty-czwartek|E:-52|Жирний четвер|Tłusty Czwartek|PL|culture|targeted\nandrzejki|11-29|Анджейки|Andrzejki|PL|culture|targeted\npolish-flag|05-02|День прапора Польщі|Polish Flag Day|PL|civic|targeted\nua-unity|01-22|День Соборності України|Unity Day of Ukraine|UA|civic|targeted\nua-heroes-hundred|02-20|День Героїв Небесної Сотні|Heavenly Hundred Heroes Day|UA|memorial|review\nua-invasion|02-24|Річниця початку повномасштабного вторгнення|Anniversary of Russia's full-scale invasion of Ukraine|UA|memorial|review\nua-crimea|02-26|День спротиву окупації Криму|Day of Resistance to the Occupation of Crimea|UA|memorial|review\nua-vyshyvanka|W:05:3:3|День вишиванки|Vyshyvanka Day|UA|culture|targeted\nua-flag|08-23|День Державного Прапора України|National Flag Day of Ukraine|UA|civic|targeted\nua-writing|10-27|День української писемності та мови|Ukrainian Writing and Language Day|UA|culture|targeted\nua-dignity|11-21|День Гідності та Свободи|Dignity and Freedom Day|UA|civic|review\nua-holodomor|W:11:5:4|День памʼяті жертв Голодоморів|Holodomor Remembrance Day|UA|memorial|review\nua-armed-forces|12-06|День Збройних Сил України|Armed Forces Day of Ukraine|UA|civic|review\nua-school|09-01|День знань|Knowledge Day|UA|school|review\nua-cosmonautics|04-12|День працівників ракетно-космічної галузі України|Space Industry Workers' Day in Ukraine|UA|career|targeted\nua-constitution|06-28|День Конституції України|Constitution Day of Ukraine|UA|statutory_ua|targeted\nua-statehood|07-15|День Української Державності|Ukrainian Statehood Day|UA|statutory_ua|targeted\nua-independence|08-24|День Незалежності України|Independence Day of Ukraine|UA|statutory_ua|targeted\nua-defenders|10-01|День захисників і захисниць України|Defenders of Ukraine Day|UA|statutory_ua|review\nua-may8|05-08|День памʼяті та перемоги над нацизмом у Другій світовій війні|Ukraine Remembrance and Victory over Nazism Day|UA|statutory_ua|review\nua-labor|05-01|День праці|Labour Day in Ukraine|UA|statutory_ua|targeted\nua-new-year|01-01|Новий рік|New Year's Day|UA|statutory_ua|off\nua-march8|03-08|Міжнародний жіночий день|International Women's Day|UA|statutory_ua|off\nua-easter|O:0|Великдень|Easter in Ukraine|UA|statutory_ua|off\nua-trinity|O:49|Трійця|Pentecost in Ukraine|UA|statutory_ua|off\nua-christmas|12-25|Різдво Христове|Christmas in Ukraine|UA|statutory_ua|off\nbirthday|USER|День народження користувача|User birthday|USER|personal|targeted\nname-day|USER|Іменини|Name day|USER|personal|targeted\nwedding|USER|Весілля|Wedding|USER|personal|targeted\nwedding-anniversary|USER|Річниця весілля|Wedding anniversary|USER|personal|targeted\nrelationship-anniversary|USER|Річниця стосунків|Relationship anniversary|USER|personal|targeted\nchild-birth|USER|Народження дитини|Birth of a child|USER|personal|targeted\nbaby-shower|USER|Свято перед народженням дитини|Baby shower|USER|personal|targeted\ngraduation|USER|Випускний|Graduation|USER|personal|targeted\nengagement|USER|Заручини|Engagement|USER|personal|targeted\nhousewarming|USER|Новосілля|Housewarming|USER|personal|targeted\nretirement|USER|Вихід на пенсію|Retirement|USER|personal|targeted\nwork-anniversary|USER|Річниця роботи|Work anniversary|USER|lifecycle|targeted\napp-anniversary|USER|Річниця реєстрації в застосунку|App signup anniversary|USER|lifecycle|targeted\ntrial-end|USER|Завершення пробного періоду|Trial ending|USER|lifecycle|off\nsubscription-renewal|USER|Поновлення підписки|Subscription renewal|USER|lifecycle|off\npersonal-memorial|USER|Памʼятна дата близької людини|Personal memorial|USER|personal|review\ncoffee-day|10-01|Міжнародний день кави|International Coffee Day|WORLD|food|targeted\npizza-us|02-09|День піци у США|National Pizza Day|US|food|targeted\nchocolate-day|07-07|Всесвітній день шоколаду|World Chocolate Day|WORLD|food|targeted\nemoji-day|07-17|Всесвітній день емодзі|World Emoji Day|WORLD|tech|targeted\nprogrammers-day|N:256|День програміста / 256-й день року|Programmers' Day|WORLD|tech|targeted\nmar10|03-10|День Маріо|MAR10 Day|WORLD|culture|review\nmartin-luther-king|W:01:0:3|День Мартіна Лютера Кінга|Martin Luther King Jr. Day|US|memorial|review\nmemorial-day-us|L:05:0|День памʼяті в США|Memorial Day|US|memorial|review\njuneteenth|06-19|Джунтінс|Juneteenth|US|civic|review\nindependence-us|07-04|День Незалежності США|Independence Day in the United States|US|civic|targeted\ncanada-day|07-01|День Канади|Canada Day|CA|civic|targeted\npolish-independence|11-11|День незалежності Польщі|Polish Independence Day|PL|civic|targeted\npolish-constitution|05-03|День Конституції 3 травня в Польщі|Polish Constitution Day|PL|civic|targeted\nvictoria-day|V:05-25|День Вікторії|Victoria Day|CA|civic|review\nlabor-us-ca|W:09:0:1|День праці в США та Канаді|Labor Day|US,CA|civic|targeted\nremembrance|11-11|День памʼяті|Remembrance Day|GB,CA,AU,NZ|memorial|review\nveterans-us|11-11|День ветеранів у США|Veterans Day|US|memorial|review\nanzac|04-25|День АНЗАК|Anzac Day|AU,NZ|memorial|review\nkwanzaa|12-26|Початок Кванзи|Kwanzaa begins|US|culture|targeted\ndog-day|08-26|День собак|Dog Day|WORLD|pets|targeted\ncat-day|08-08|Міжнародний день котів|International Cat Day|WORLD|pets|targeted\nworld-animal-day|10-04|Всесвітній день тварин|World Animal Day|WORLD|pets|targeted\n".splitlines():
    fields=line.split('|')
    src={'music-day-june':MUSIC,'music-day-oct':'https://imc-cim.org/international-music-day/','victoria-day':'https://www.canada.ca/en/canadian-heritage/services/important-commemorative-days.html','coffee-day':'https://ico.org/international-coffee-day/','jazz-day':UN,'womens-day':UN,'giving-tuesday':'https://www.givingtuesday.org/','polish-independence':PKG_SOURCE['PL'],'polish-constitution':PKG_SOURCE['PL']}.get(fields[0],'')
    add_def(*fields,source=src)
for line in "01-04|Всесвітній день азбуки Брайля|World Braille Day\n01-24|Міжнародний день освіти|International Day of Education\n01-27|Міжнародний день памʼяті жертв Голокосту|International Holocaust Remembrance Day|review\n02-02|Всесвітній день водно-болотних угідь|World Wetlands Day\n02-04|Міжнародний день людського братерства|International Day of Human Fraternity\n02-11|Міжнародний день жінок і дівчат у науці|International Day of Women and Girls in Science\n02-13|Всесвітній день радіо|World Radio Day\n02-20|Всесвітній день соціальної справедливості|World Day of Social Justice\n02-21|Міжнародний день рідної мови|International Mother Language Day\n03-03|Всесвітній день дикої природи|World Wildlife Day\n03-20|Міжнародний день щастя|International Day of Happiness\n03-21|Всесвітній день поезії|World Poetry Day\n03-21|Міжнародний день лісів|International Day of Forests\n03-21|Всесвітній день людей із синдромом Дауна|World Down Syndrome Day|review\n03-21|Міжнародний день боротьби за ліквідацію расової дискримінації|International Day for the Elimination of Racial Discrimination|review\n03-22|Всесвітній день води|World Water Day\n03-23|Всесвітній метеорологічний день|World Meteorological Day\n03-24|Всесвітній день боротьби з туберкульозом|World Tuberculosis Day|review\n04-02|Всесвітній день поширення інформації про аутизм|World Autism Awareness Day|review\n04-06|Міжнародний день спорту на благо розвитку та миру|International Day of Sport for Development and Peace\n04-07|Всесвітній день здоровʼя|World Health Day|review\n04-12|Міжнародний день польоту людини в космос|International Day of Human Space Flight\n04-22|Міжнародний день Матері-Землі|International Mother Earth Day\n04-23|Всесвітній день книги й авторського права|World Book and Copyright Day\n04-26|Всесвітній день інтелектуальної власності|World Intellectual Property Day\n04-28|Всесвітній день охорони праці|World Day for Safety and Health at Work|review\n05-03|Всесвітній день свободи преси|World Press Freedom Day\n05-15|Міжнародний день сімʼї|International Day of Families\n05-16|Міжнародний день світла|International Day of Light\n05-17|Всесвітній день електрозвʼязку та інформаційного суспільства|World Telecommunication and Information Society Day\n05-20|Всесвітній день бджіл|World Bee Day\n05-21|Всесвітній день культурного різноманіття|World Day for Cultural Diversity for Dialogue and Development\n05-22|Міжнародний день біологічного різноманіття|International Day for Biological Diversity\n05-31|Всесвітній день без тютюну|World No Tobacco Day|review\n06-01|Всесвітній день батьків|Global Day of Parents\n06-03|Всесвітній день велосипеда|World Bicycle Day\n06-05|Всесвітній день довкілля|World Environment Day\n06-07|Всесвітній день безпечності харчових продуктів|World Food Safety Day|review\n06-08|Всесвітній день океанів|World Oceans Day\n06-11|Міжнародний день гри|International Day of Play\n06-12|Всесвітній день боротьби з дитячою працею|World Day Against Child Labour|review\n06-14|Всесвітній день донора крові|World Blood Donor Day|review\n06-20|Всесвітній день біженців|World Refugee Day|review\n06-21|Міжнародний день йоги|International Day of Yoga\n06-27|День мікро-, малих та середніх підприємств|Micro-, Small and Medium-sized Enterprises Day\n06-30|Міжнародний день астероїда|International Asteroid Day\n07-11|Всесвітній день народонаселення|World Population Day|review\n07-15|Всесвітній день навичок молоді|World Youth Skills Day\n07-18|Міжнародний день Нельсона Мандели|Nelson Mandela International Day\n07-20|Міжнародний день шахів|World Chess Day\n07-20|Міжнародний день Місяця|International Moon Day\n07-30|Міжнародний день дружби|International Day of Friendship\n08-09|Міжнародний день корінних народів світу|International Day of the World's Indigenous Peoples|review\n08-11|Всесвітній день стилпана|World Steelpan Day\n08-12|Міжнародний день молоді|International Youth Day\n08-19|Всесвітній день гуманітарної допомоги|World Humanitarian Day|review\n09-05|Міжнародний день благодійності|International Day of Charity\n09-08|Міжнародний день грамотності|International Literacy Day\n09-15|Міжнародний день демократії|International Day of Democracy\n09-16|Міжнародний день охорони озонового шару|International Day for the Preservation of the Ozone Layer\n09-21|Міжнародний день миру|International Day of Peace|review\n09-23|Міжнародний день жестових мов|International Day of Sign Languages\n09-27|Всесвітній день туризму|World Tourism Day\n09-29|Міжнародний день обізнаності про втрати та марнування їжі|International Day of Awareness of Food Loss and Waste|review\n09-30|Міжнародний день перекладу|International Translation Day\n10-01|Міжнародний день людей старшого віку|International Day of Older Persons\n10-02|Міжнародний день ненасильства|International Day of Non-Violence|review\n10-05|Всесвітній день учителів|World Teachers' Day\n10-09|Всесвітній день пошти|World Post Day\n10-10|Всесвітній день психічного здоровʼя|World Mental Health Day|review\n10-11|Міжнародний день дівчат|International Day of the Girl Child|review\n10-13|Міжнародний день зменшення ризику стихійних лих|International Day for Disaster Risk Reduction|review\n10-15|Міжнародний день сільських жінок|International Day of Rural Women\n10-16|Всесвітній день продовольства|World Food Day|review\n10-17|Міжнародний день боротьби з бідністю|International Day for the Eradication of Poverty|review\n10-24|День ООН|United Nations Day\n10-31|Всесвітній день міст|World Cities Day\n11-05|Всесвітній день поширення інформації про цунамі|World Tsunami Awareness Day|review\n11-10|Всесвітній день науки за мир і розвиток|World Science Day for Peace and Development\n11-14|Всесвітній день боротьби з діабетом|World Diabetes Day|review\n11-16|Міжнародний день толерантності|International Day for Tolerance\n11-19|Всесвітній день туалету|World Toilet Day|review\n11-20|Всесвітній день дитини|World Children's Day\n11-21|Всесвітній день телебачення|World Television Day\n11-25|Міжнародний день боротьби за ліквідацію насильства щодо жінок|International Day for the Elimination of Violence against Women|review\n12-01|Всесвітній день боротьби зі СНІДом|World AIDS Day|review\n12-03|Міжнародний день людей з інвалідністю|International Day of Persons with Disabilities|review\n12-05|Міжнародний день волонтерів|International Volunteer Day\n12-05|Всесвітній день ґрунтів|World Soil Day\n12-07|Міжнародний день цивільної авіації|International Civil Aviation Day\n12-09|Міжнародний день боротьби з корупцією|International Anti-Corruption Day|review\n12-10|День прав людини|Human Rights Day|review\n12-11|Міжнародний день гір|International Mountain Day\n12-18|Міжнародний день мігрантів|International Migrants Day|review\n12-20|Міжнародний день солідарності людей|International Human Solidarity Day\n".splitlines():
    when,uk,en,*policy=line.split('|')
    add_def('un-'+slug(en),when,uk,en,'WORLD','un',*(policy or ['targeted']))

regional_faith=[
 ('lunar-new-year','Місячний Новий рік','Lunar New Year','CN','Chinese New Year (Spring Festival)','CN,SG,MY,TW,HK,MO'),
 ('tet','Тет','Tết','VN','Lunar New Year','VN'),
 ('seollal','Соллаль','Seollal','KR','Korean New Year','KR'),
 ('dragon-boat','Свято човнів-драконів','Dragon Boat Festival','CN','Dragon Boat Festival','CN,TW,HK,MO'),
 ('mid-autumn','Свято середини осені','Mid-Autumn Festival','CN','Mid-Autumn Festival','CN,TW,SG,MY,VN,HK,MO'),
 ('holi','Холі','Holi','IN','Holi','IN'),
 ('diwali','Дівалі','Diwali','IN','Diwali','IN'),
 ('dussehra','Дуссехра','Dussehra','IN','Dussehra','IN'),
 ('theravada-vesak','Весак','Vesak','ID','Vesak Day','ID'),
 ('nyepi','Ньєпі','Nyepi','ID','Day of Silence','ID'),
 ('eid-fitr-indonesia','Ід аль-Фітр в Індонезії','Eid al-Fitr in Indonesia','ID','Eid al-Fitr','ID'),
 ('eid-adha-indonesia','Ід аль-Адха в Індонезії','Eid al-Adha in Indonesia','ID','Eid al-Adha','ID'),
 ('eid-fitr-india','Ід аль-Фітр в Індії','Eid al-Fitr in India','IN','Eid al-Fitr','IN'),
 ('eid-adha-india','Ід аль-Адха в Індії','Eid al-Adha in India','IN','Eid al-Adha','IN'),
 ('rosh-hashanah','Рош га-Шана','Rosh Hashanah','IL','Rosh Hashanah','IL'),
 ('yom-kippur','Йом Кіпур','Yom Kippur','IL','Yom Kippur','IL'),
 ('passover','Песах','Passover','IL','Pesach','IL'),
 ('sukkot','Суккот','Sukkot','IL','Sukkot','IL'),
 ('songkran','Сонгкран','Songkran','TH','Songkran Festival','TH'),
]
for key,uk,en,c,match,markets in regional_faith:
    h=holidays.country_holidays(c,years=years,observed=False,language='en_US')
    dates=[]
    for y in years:
        choices=sorted(d for d in h if d.year==y and any(s.removesuffix(' (estimated)')==match for s in h.get_list(d)))
        if choices: dates.append(choices[0].isoformat())
    if not dates:
        print('Missing faith match',key,[v for v in list(h.values())[:30]])
        continue
    add_def(key,'D:'+','.join(dates),uk,en,markets,'faith','review',PKG,'Дати для зазначеного ринку або календарної традиції. Перевірити місцеву дату й початок за місцевим часом.')
add_def('ramadan-first-fast','D:2026-02-18,2027-02-08,2028-01-28','Перший день посту Рамадану','First day of Ramadan fasting','WORLD','faith','review',FAITH,'Орієнтовна цивільна дата першого дня посту. Початок Рамадану після заходу сонця напередодні. Дату підтвердити локально.')
add_def('hanukkah-first-day','D:2026-12-05,2027-12-25,2028-12-13','Ханука','Hanukkah','WORLD','faith','review','https://www.hebcal.com/holidays/chanukah','Перший повний цивільний день. Початок після заходу сонця напередодні.',length=8)
for key,uk,en in [('super-bowl','Супербоул','Super Bowl'),('oktoberfest','Октоберфест','Oktoberfest'),('earth-hour','Година Землі','Earth Hour'),('eurovision','Євробачення','Eurovision Song Contest'),('world-cup','Чемпіонат світу з футболу','FIFA World Cup'),('olympics','Олімпійські ігри','Olympic Games'),('company-anniversary','Річниця компанії','Company anniversary'),('city-day','День міста','City day'),('back-to-school','Початок навчального року','Back-to-school'),('prime-day','Prime Day','Prime Day')]:
    defs.append([key,'EXTERNAL','CONFIGURED','event',uk,en,'review',14,3,'Підібрати музику під формат події.','','Завантажити конкретну дату та ринок з календаря організатора або конфігурації.'])

countries=holidays.list_supported_countries()
generated=set()
errors=[]
supported=set()
for c in sorted(k for k in countries if len(k)==2 and k not in {'UA','UK'}):
    configurations=[(None,c)]
    if c=='GB':
        configurations += [(s,f'GB-{s}') for s in ('ENG','NIR','SCT','WLS')]
    base_set=set()
    for sub,market in configurations:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                h=holidays.country_holidays(c,subdiv=sub,years=years,observed=False,language='en_US',expand=False)
                local_h=holidays.country_holidays(c,subdiv=sub,years=years,observed=False,expand=False)
        except (NotImplementedError,ValueError,OverflowError) as exc:
            errors.append([market,str(exc)])
            continue
        for day in sorted(h):
            if day.year not in years:
                continue
            names=h.get_list(day)
            localnames=local_h.get_list(day) if day in local_h else []
            # Joined local text keeps every co-occurring label without assuming label order aligns across languages.
            note_base='Дані довідника для ринку. Переноси вихідних і робочий графік перевіряти окремо.'
            if localnames and localnames!=names:
                note_base+=' Місцева назва або назви цієї дати: '+ ' / '.join(localnames)
            for name in names:
                item=(day,name)
                if sub and item in base_set:
                    continue
                if not sub:
                    base_set.add(item)
                normalized=re.sub(r'\s+\(estimated\)$','',name,flags=re.I)
                digest=hashlib.sha256(normalized.casefold().encode()).hexdigest()[:10]
                key='public-'+market.lower()+'-'+slug(normalized)+'-'+digest
                unique=(key,day)
                if unique in generated:
                    continue
                generated.add(unique)
                supported.add(c)
                source=PKG_SOURCE.get(c,PKG)
                status='provider_estimate' if 'estimated' in name.lower() else 'provider'
                if re.match(r'^(day off|substitute|observed)\b',name,re.I) or re.search(r'\((observed|substitute day)\)',name,re.I):
                    status='provider_substitute'
                add_occ(key,day,day,market,'public_holiday','',name,status,'off','','','',source,note_base)
supported.add('UA')
occ.sort(key=lambda row:(row[2],row[4],row[5],row[1]))
assert len(occ)==len({r[0] for r in occ})
assert len(defs)==len({r[0] for r in defs})
assert sum(r[1]=='black-friday' and r[2]=='2027-11-26' for r in occ)==1
assert sum(r[1]=='ua-easter' and r[2]=='2027-05-02' for r in occ)==1
assert ('PL','2027-12-24','Christmas Eve') in {(r[4],r[2],r[7]) for r in occ}
assert all(date.fromisoformat(r[2])<=date.fromisoformat(r[3]) for r in occ)
assert all(r[9]!='off' or r[10]==r[11]==r[12]=='' for r in occ)
with (out/'holiday-occurrences-2026-2028.csv').open('w',encoding='utf-8',newline='') as handle:
    writer=csv.writer(handle)
    writer.writerow(cols)
    writer.writerows(occ)
print(len(occ),len(defs),len(supported),len(errors))
print(errors[:10])
