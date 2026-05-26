"""
閲嶆柊鐢熸垚 LP12-LP18 鐨勯珮璐ㄩ噺涔犻
鍏堝垹闄ゆ棫鐨勫瀮鍦鹃鐩紝鐒跺悗鏍规嵁璇剧▼鍐呭鐢熸垚鏂伴鐩?
"""
import sqlite3
import random
from datetime import datetime

def get_db():
    return sqlite3.connect('instance/testmaster.db')

def delete_bad_exercises(lp_id):
    """鍒犻櫎鎸囧畾LP鐨勫崰浣嶇鍨冨溇棰樼洰"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM exercises
        WHERE learning_path_id = ?
        AND description LIKE '%閫夐」A%'
        AND description LIKE '%閫夐」B%'
        AND description LIKE '%閫夐」C%'
        AND description LIKE '%閫夐」D%'
    """, (lp_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def insert_exercise(cursor, title, description, solution, exercise_type, difficulty, learning_path_id, category, lang="涓枃"):
    """???????"""
    cursor.execute("""
        INSERT INTO exercises
        (title, description, solution, exercise_type, difficulty,
         learning_path_id, category, is_public, language,
         created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, datetime('now'), datetime('now'))
    """, (title, description, solution, exercise_type, difficulty, learning_path_id, category, lang))

# ============== LP12: 绉诲姩绔祴璇曞熀纭€ ==============
def generate_lp12_exercises(cursor):
    exercises = [
        # 绉诲姩绔祴璇曟杩?
        {
            "title": "Android鍜宨OS骞冲彴鍦ㄥ簲鐢ㄥ彂甯冨鏍告満鍒朵笂鐨勪富瑕佸尯鍒槸浠€涔堬紵",
            "desc": "Android鍜宨OS骞冲彴鍦ㄥ簲鐢ㄥ彂甯冨鏍告満鍒朵笂鐨勪富瑕佸尯鍒槸浠€涔堬紵\n\nA. Android搴旂敤鏃犻渶瀹℃牳鍗冲彲鐩存帴鍙戝竷鍒癎oogle Play锛宨OS搴旂敤闇€瑕佺粡杩嘇pple涓ユ牸鐨勫鏍告祦绋媆nB. iOS搴旂敤閫氬父瀹℃牳鍛ㄦ湡涓?-2澶╋紝Android搴旂敤瀹℃牳鍛ㄦ湡涓?-7澶‐nC. 涓や釜骞冲彴閮介噰鐢ㄥ畬鍏ㄧ浉鍚岀殑鑷姩鍖栧鏍告満鍒讹紝娌℃湁浜哄伐浠嬪叆\nD. Android鍜宨OS鐨勫鏍告爣鍑嗗拰娴佺▼瀹屽叏涓€鑷达紝涓昏妫€鏌ュ唴瀹规槸鍚﹀悎瑙?",
            "sol": "A",
            "type": "single_choice",
            "diff": "medium",
            "cat": "绉诲姩绔祴璇曟杩?"
        },
        {
            "title": "浠ヤ笅鍝」涓嶆槸绉诲姩绔祴璇曠浉杈冧簬Web绔祴璇曠殑鐗规畩鎸戞垬锛?",
            "desc": "浠ヤ笅鍝」涓嶆槸绉诲姩绔祴璇曠浉杈冧簬Web绔祴璇曠殑鐗规畩鎸戞垬锛焅n\nA. 璁惧纰庣墖鍖栵紝闇€瑕侀€傞厤澶氱灞忓箷灏哄鍜屽垎杈ㄧ巼\nB. 缃戠粶鐜澶嶆潅锛岄渶瑕佸鐞嗗急缃戙€佹柇缃戙€佺綉缁滃垏鎹㈢瓑鍦烘櫙\nC. 娴忚鍣ㄥ吋瀹规€ч棶棰橈紝闇€瑕侀€傞厤Chrome銆丗irefox銆丼afari绛塡nD. 绯荤粺璧勬簮鏈夐檺锛岄渶瑕佸叧娉ㄥ唴瀛樸€佺數閲忋€丆PU绛夋€ц兘鎸囨爣",
            "sol": "C",
            "type": "single_choice",
            "diff": "easy",
            "cat": "绉诲姩绔祴璇曟杩?"
        },
        {
            "title": "绉诲姩绔簲鐢ㄧ殑銆屽畨瑁呭寘澶у皬銆嶄紭鍖栦富瑕佽€冭檻鍝簺鍥犵礌锛?",
            "desc": "绉诲姩绔簲鐢ㄧ殑銆屽畨瑁呭寘澶у皬銆嶄紭鍖栦富瑕佽€冭檻鍝簺鍥犵礌锛焅n\nA. 涓昏鑰冭檻浠ｇ爜琛屾暟锛屼唬鐮佽秺灏戝寘瓒婂皬\nB. 闇€瑕佽€冭檻鍥剧墖璧勬簮鍘嬬缉銆佷唬鐮佹贩娣嗐€佹棤鐢ㄨ祫婧愮Щ闄ゃ€乻o搴撹繃婊ょ瓑澶氫釜鏂归潰\nC. 鍙渶瑕佸帇缂╁浘鐗囪祫婧愬嵆鍙紝鍏朵粬鍥犵礌褰卞搷涓嶅ぇ\nD. 瀹夎鍖呭ぇ灏忓鐢ㄦ埛浣撻獙娌℃湁褰卞搷锛屼笉闇€瑕佷紭鍖?",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "绉诲姩绔祴璇曟杩?"
        },
        {
            "title": "鍏充簬绉诲姩绔簲鐢ㄧ殑鐢熷懡鍛ㄦ湡娴嬭瘯锛屼互涓嬭娉曟纭殑鏄紵",
            "desc": "鍏充簬绉诲姩绔簲鐢ㄧ殑鐢熷懡鍛ㄦ湡娴嬭瘯锛屼互涓嬭娉曟纭殑鏄紵\n\nA. 鍙渶瑕佹祴璇曞簲鐢ㄥ惎鍔ㄥ拰閫€鍑轰袱涓姸鎬乗nB. 闇€瑕佹祴璇曞惎鍔ㄣ€佸墠鍙拌繍琛屻€佸悗鍙拌繍琛屻€佹寕璧枫€佹仮澶嶃€佺粓姝㈢瓑澶氱鐘舵€佺殑杞崲\nC. 搴旂敤鐢熷懡鍛ㄦ湡娴嬭瘯鍙湪iOS涓婇渶瑕侊紝Android涓嶉渶瑕乗nD. 鐢熷懡鍛ㄦ湡娴嬭瘯鏄紑鍙戜汉鍛樼殑鑱岃矗锛屼笌娴嬭瘯浜哄憳鏃犲叧",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "绉诲姩绔祴璇曟杩?"
        },
        {
            "title": "浠ヤ笅鍝簺鏄Щ鍔ㄧ娴嬭瘯闇€瑕佽鐩栫殑鍏稿瀷鍦烘櫙锛?",
            "desc": "浠ヤ笅鍝簺鏄Щ鍔ㄧ娴嬭瘯闇€瑕佽鐩栫殑鍏稿瀷鍦烘櫙锛燂紙澶氶€夛級\n\nA. 妯珫灞忓垏鎹nB. 鏉ョ數/鐭俊涓柇\nC. 浣庣數閲忔ā寮廫nD. 澶滈棿妯″紡鍒囨崲",
            "sol": "A,B,C,D",
            "type": "multiple_choice",
            "diff": "easy",
            "cat": "绉诲姩绔祴璇曟杩?"
        },
        # 绉诲姩绔姛鑳芥祴璇?
        {
            "title": "绉诲姩绔姛鑳芥祴璇曚腑锛?鎵嬪娍鎿嶄綔'娴嬭瘯涓昏鍖呮嫭鍝簺鍐呭锛?",
            "desc": "绉诲姩绔姛鑳芥祴璇曚腑锛?鎵嬪娍鎿嶄綔'娴嬭瘯涓昏鍖呮嫭鍝簺鍐呭锛焅n\nA. 浠呮祴璇曠偣鍑绘搷浣淺nB. 鍖呮嫭鐐瑰嚮銆侀暱鎸夈€佹粦鍔ㄣ€佹崗鍚堛€佹嫋鎷姐€佸弻鍑荤瓑澶氱鎵嬪娍\nC. 鎵嬪娍鎿嶄綔涓嶉渶瑕佷笓闂ㄦ祴璇曪紝涓嶹eb绔偣鍑荤浉鍚孿nD. 鍙渶瑕佹祴璇旳ndroid绯荤粺鐨勬墜鍔匡紝iOS涓嶉渶瑕?",
            "sol": "B",
            "type": "single_choice",
            "diff": "easy",
            "cat": "绉诲姩绔姛鑳芥祴璇?"
        },
        {
            "title": "绉诲姩绔簲鐢ㄧ殑銆屾潈闄愭祴璇曘€嶉渶瑕佸叧娉ㄥ摢浜涙柟闈紵",
            "desc": "绉诲姩绔簲鐢ㄧ殑銆屾潈闄愭祴璇曘€嶉渶瑕佸叧娉ㄥ摢浜涙柟闈紵\n\nA. 鍙渶瑕佹祴璇曞簲鐢ㄥ惎鍔ㄦ椂鐢宠鐨勬潈闄怽nB. 闇€瑕佹祴璇曟潈闄愮敵璇锋椂鏈恒€佹潈闄愭嫆缁濆悗鐨勫鐞嗐€佹潈闄愬姩鎬佸彉鍖栥€佺郴缁熻缃腑淇敼鏉冮檺鍚庣殑琛屼负绛塡nC. 鏉冮檺娴嬭瘯鏄痠OS鐙湁鐨勶紝Android涓嶉渶瑕乗nD. 鏉冮檺娴嬭瘯鍙渶瑕侀獙璇佷竴娆★紝涓嶉渶瑕佸弽澶嶆祴璇?",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "绉诲姩绔姛鑳芥祴璇?"
        },
        {
            "title": "鍏充簬绉诲姩绔€屾帹閫侀€氱煡銆嶆祴璇曪紝浠ヤ笅璇存硶閿欒鐨勬槸锛?",
            "desc": "鍏充簬绉诲姩绔€屾帹閫侀€氱煡銆嶆祴璇曪紝浠ヤ笅璇存硶閿欒鐨勬槸锛焅n\nA. 闇€瑕佹祴璇曢€氱煡鐨勫埌杈剧巼銆佹樉绀哄唴瀹广€佺偣鍑昏烦杞€昏緫\nB. 闇€瑕佹祴璇曢€氱煡鍦ㄩ攣灞忋€侀€氱煡鏍忋€佸簲鐢ㄥ唴绛変笉鍚屽満鏅笅鐨勮〃鐜癨nC. 鎺ㄩ€侀€氱煡娴嬭瘯鍙渶瑕佸湪WiFi鐜涓嬭繘琛屽嵆鍙痋nD. 闇€瑕佹祴璇曢€氱煡鐨勯潤闊虫ā寮忋€佸厤鎵撴壈妯″紡涓嬬殑琛屼负",
            "sol": "C",
            "type": "single_choice",
            "diff": "easy",
            "cat": "绉诲姩绔姛鑳芥祴璇?"
        },
        {
            "title": "绉诲姩绔?瀹夎/鍗歌浇/鍗囩骇'娴嬭瘯闇€瑕侀獙璇佸摢浜涘満鏅紵",
            "desc": "绉诲姩绔?瀹夎/鍗歌浇/鍗囩骇'娴嬭瘯闇€瑕侀獙璇佸摢浜涘満鏅紵锛堝閫夛級\n\nA. 棣栨瀹夎鍜岃鐩栧畨瑁匼nB. 搴旂敤鍗歌浇鍚庢暟鎹槸鍚︽竻闄ゅ共鍑€\nC. 浣庣増鏈崌绾у埌鏂扮増鏈殑鍏煎鎬nD. 瀹夎杩囩▼涓潵鐢典腑鏂殑澶勭悊",
            "sol": "A,B,C,D",
            "type": "multiple_choice",
            "diff": "medium",
            "cat": "绉诲姩绔姛鑳芥祴璇?"
        },
        {
            "title": "绉诲姩绔€屽悗鍙拌繍琛屻€嶆祴璇曚富瑕佸叧娉ㄤ粈涔堬紵",
            "desc": "绉诲姩绔€屽悗鍙拌繍琛屻€嶆祴璇曚富瑕佸叧娉ㄤ粈涔堬紵\n\nA. 搴旂敤鍦ㄥ悗鍙版椂鏄惁缁х画鍗犵敤澶ч噺CPU\nB. 搴旂敤鍦ㄥ悗鍙颁竴娈垫椂闂村悗鍐嶆鎵撳紑鏄惁闇€瑕侀噸鏂扮櫥褰昞nC. 搴旂敤鍦ㄥ悗鍙版椂鎺ㄩ€侀€氱煡鏄惁杩樿兘姝ｅ父鎺ユ敹\nD. 浠ヤ笂鎵€鏈夐€夐」閮芥槸鍚庡彴杩愯娴嬭瘯闇€瑕佸叧娉ㄧ殑",
            "sol": "D",
            "type": "single_choice",
            "diff": "medium",
            "cat": "绉诲姩绔姛鑳芥祴璇?"
        },
        # 鍏煎鎬ф祴璇?
        {
            "title": "Android纰庣墖鍖栭棶棰樹富瑕佷綋鐜板湪鍝簺鏂归潰锛?",
            "desc": "Android纰庣墖鍖栭棶棰樹富瑕佷綋鐜板湪鍝簺鏂归潰锛燂紙澶氶€夛級\n\nA. 鎿嶄綔绯荤粺鐗堟湰浼楀锛圓ndroid 8/9/10/11/12/13/14绛夛級\nB. 璁惧鍘傚晢浼楀锛屾瘡涓巶鍟嗛兘鏈夊畾鍒禪I\nC. 灞忓箷灏哄鍜屽垎杈ㄧ巼宸紓宸ㄥぇ\nD. 纭欢閰嶇疆宸紓锛堝唴瀛樸€丆PU銆佹憚鍍忓ご绛夛級",
            "sol": "A,B,C,D",
            "type": "multiple_choice",
            "diff": "easy",
            "cat": "鍏煎鎬ф祴璇?"
        },
        {
            "title": "绉诲姩绔吋瀹规€ф祴璇曚腑锛?灞忓箷閫傞厤'娴嬭瘯闇€瑕佸叧娉ㄥ摢浜涘唴瀹癸紵",
            "desc": "绉诲姩绔吋瀹规€ф祴璇曚腑锛?灞忓箷閫傞厤'娴嬭瘯闇€瑕佸叧娉ㄥ摢浜涘唴瀹癸紵\n\nA. 鍙渶瑕佸湪澶у睆鎵嬫満涓婃祴璇曞嵆鍙痋nB. 闇€瑕佸湪涓嶅悓鍒嗚鲸鐜囥€佷笉鍚屽睆骞曟瘮渚嬨€佷笉鍚孌PI鐨勮澶囦笂娴嬭瘯UI鏄剧ず\nC. 灞忓箷閫傞厤鍙渶瑕佹祴璇曠珫灞忥紝妯睆涓嶉渶瑕佹祴璇昞nD. 灞忓箷閫傞厤鏄璁″笀鐨勮亴璐ｏ紝娴嬭瘯涓嶉渶瑕佸叧娉?",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "鍏煎鎬ф祴璇?"
        },
        {
            "title": "iOS搴旂敤鐨勫吋瀹规€ф祴璇曠浉姣擜ndroid鐨勪紭鍔垮湪浜庯紵",
            "desc": "iOS搴旂敤鐨勫吋瀹规€ф祴璇曠浉姣擜ndroid鐨勪紭鍔垮湪浜庯紵\n\nA. iOS璁惧鍨嬪彿鏇村锛屾祴璇曡鐩栭潰鏇村箍\nB. iOS绯荤粺鐗堟湰鍜屾満鍨嬬浉瀵归泦涓紝纰庣墖鍖栫▼搴﹁緝浣嶾nC. iOS涓嶉渶瑕佸吋瀹规€ф祴璇曪紝鎵€鏈夎澶囪〃鐜颁竴鑷碶nD. iOS搴旂敤鍙兘鍦ㄦ渶鏂扮郴缁熶笂杩愯",
            "sol": "B",
            "type": "single_choice",
            "diff": "easy",
            "cat": "鍏煎鎬ф祴璇?"
        },
        {
            "title": "绉诲姩绔吋瀹规€ф祴璇曟椂锛屼互涓嬪摢娆惧伐鍏峰彲浠ョ敤浜庤繙绋嬬湡鏈烘祴璇曪紵",
            "desc": "绉诲姩绔吋瀹规€ф祴璇曟椂锛屼互涓嬪摢娆惧伐鍏峰彲浠ョ敤浜庤繙绋嬬湡鏈烘祴璇曪紵\n\nA. Postman\nB. JMeter\nC. BrowserStack 鎴?Sauce Labs\nD. Charles",
            "sol": "C",
            "type": "single_choice",
            "diff": "easy",
            "cat": "鍏煎鎬ф祴璇?"
        },
        {
            "title": "鍦ㄨ繘琛岀Щ鍔ㄧ鍏煎鎬ф祴璇曟椂锛屼互涓嬪摢椤逛笉灞炰簬蹇呴』娴嬭瘯鐨勫唴瀹癸紵",
            "desc": "鍦ㄨ繘琛岀Щ鍔ㄧ鍏煎鎬ф祴璇曟椂锛屼互涓嬪摢椤逛笉灞炰簬蹇呴』娴嬭瘯鐨勫唴瀹癸紵\n\nA. 涓嶅悓鎿嶄綔绯荤粺鐗堟湰涓婄殑鍔熻兘琛ㄧ幇\nB. 涓嶅悓鍝佺墝璁惧涓婄殑UI鏄剧ず\nC. 搴旂敤浠ｇ爜鐨勫湀澶嶆潅搴nD. 涓嶅悓缃戠粶鐜涓嬬殑琛ㄧ幇",
            "sol": "C",
            "type": "single_choice",
            "diff": "easy",
            "cat": "鍏煎鎬ф祴璇?"
        },
        # 寮辩綉娴嬭瘯
        {
            "title": "寮辩綉娴嬭瘯涓父鐢ㄧ殑缃戠粶妯℃嫙宸ュ叿鍖呮嫭鍝簺锛?",
            "desc": "寮辩綉娴嬭瘯涓父鐢ㄧ殑缃戠粶妯℃嫙宸ュ叿鍖呮嫭鍝簺锛燂紙澶氶€夛級\n\nA. Charles Proxy\nB. Fiddler\nC. Chrome DevTools Network Throttling\nD. Xcode Network Link Conditioner",
            "sol": "A,B,C,D",
            "type": "multiple_choice",
            "diff": "medium",
            "cat": "寮辩綉娴嬭瘯"
        },
        {
            "title": "绉诲姩绔簲鐢ㄥ湪缃戠粶浠嶹iFi鍒囨崲鍒?G鏃讹紝搴旇鍏峰浠€涔堣兘鍔涳紵",
            "desc": "绉诲姩绔簲鐢ㄥ湪缃戠粶浠嶹iFi鍒囨崲鍒?G鏃讹紝搴旇鍏峰浠€涔堣兘鍔涳紵\n\nA. 鐩存帴闂€€锛屾彁閱掔敤鎴峰垏鎹㈢綉缁淺nB. 鑷姩妫€娴嬬綉缁滃彉鍖栧苟鎭㈠鏁版嵁浼犺緭锛屼笉闇€瑕佺敤鎴烽噸鏂版搷浣淺nC. 鎻愮ず鐢ㄦ埛閲嶅惎搴旂敤\nD. 娌℃湁浠讳綍鎻愮ず锛岀洿鎺ユ柇寮€鎵€鏈夎繛鎺?",
            "sol": "B",
            "type": "single_choice",
            "diff": "easy",
            "cat": "寮辩綉娴嬭瘯"
        },
        {
            "title": "鍦?G缃戠粶鐜涓嬫祴璇曠Щ鍔ㄧ搴旂敤锛屼富瑕佸叧娉ㄤ粈涔堬紵",
            "desc": "鍦?G缃戠粶鐜涓嬫祴璇曠Щ鍔ㄧ搴旂敤锛屼富瑕佸叧娉ㄤ粈涔堬紵\n\nA. 搴旂敤鐨勫惎鍔ㄩ€熷害鏄惁澶熷揩\nB. 瓒呮椂澶勭悊鏄惁鍚堢悊锛屾槸鍚︽湁鍙嬪ソ鐨勫姞杞芥彁绀篭nC. 楂樻竻鍥剧墖鐨勬樉绀烘晥鏋淺nD. 瑙嗛鎾斁鐨勬祦鐣呭害",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "寮辩綉娴嬭瘯"
        },
        {
            "title": "绉诲姩绔€岀绾挎ā寮忋€嶆祴璇曢渶瑕侀獙璇佸摢浜涘姛鑳斤紵",
            "desc": "绉诲姩绔€岀绾挎ā寮忋€嶆祴璇曢渶瑕侀獙璇佸摢浜涘姛鑳斤紵\n\nA. 搴旂敤鍦ㄦ棤缃戠粶鏃舵槸鍚︾洿鎺ュ穿婧僜nB. 搴旂敤鍦ㄦ棤缃戠粶鏃舵槸鍚﹁兘灞曠ず缂撳瓨鏁版嵁锛屾搷浣滄槸鍚︽湁鍚堥€傜殑鎻愮ず\nC. 绂荤嚎妯″紡涓嶉渶瑕佹祴璇曪紝鐜颁唬搴旂敤閮藉繀椤昏仈缃慭nD. 鍙渶瑕佹祴璇昗iFi鏂紑鐨勬儏鍐碉紝涓嶉渶瑕佹祴璇曡渹绐濈綉缁?",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "寮辩綉娴嬭瘯"
        },
        {
            "title": "寮辩綉娴嬭瘯涓紝'瓒呮椂銆屽拰銆嶉噸璇?鏈哄埗鐨勮璁″師鍒欐槸浠€涔堬紵",
            "desc": "寮辩綉娴嬭瘯涓紝'瓒呮椂銆屽拰銆嶉噸璇?鏈哄埗鐨勮璁″師鍒欐槸浠€涔堬紵\n\nA. 瓒呮椂鏃堕棿瓒婇暱瓒婂ソ锛岄伩鍏嶉绻侀噸璇昞nB. 璁剧疆鍚堢悊鐨勮秴鏃舵椂闂达紙濡?0-30绉掞級锛屽苟瀹炵幇鎸囨暟閫€閬块噸璇曠瓥鐣nC. 涓嶉渶瑕佽缃秴鏃讹紝绛夊緟缃戠粶鎭㈠鍗冲彲\nD. 姣忔澶辫触鍚庣珛鍗抽噸璇曪紝涓嶉渶瑕侀棿闅?",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "寮辩綉娴嬭瘯"
        },
        # Appium鑷姩鍖?
        {
            "title": "Appium鏀寔鍝簺缂栫▼璇█缂栧啓娴嬭瘯鑴氭湰锛?",
            "desc": "Appium鏀寔鍝簺缂栫▼璇█缂栧啓娴嬭瘯鑴氭湰锛燂紙澶氶€夛級\n\nA. Java\nB. Python\nC. JavaScript\nD. Ruby",
            "sol": "A,B,C,D",
            "type": "multiple_choice",
            "diff": "easy",
            "cat": "Appium鑷姩鍖?"
        },
        {
            "title": "Appium鐨勫簳灞備娇鐢ㄧ殑鏄摢绉嶅崗璁笌璁惧杩涜閫氫俊锛?",
            "desc": "Appium鐨勫簳灞備娇鐢ㄧ殑鏄摢绉嶅崗璁笌璁惧杩涜閫氫俊锛焅n\nA. HTTP鍗忚\nB. WebDriver鍗忚\nC. WebSocket鍗忚\nD. gRPC鍗忚",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "Appium鑷姩鍖?"
        },
        {
            "title": "鍦ˋppium涓紝'Accessibility ID'鏄粈涔堝畾浣嶆柟寮忥紵",
            "desc": "鍦ˋppium涓紝'Accessibility ID'鏄粈涔堝畾浣嶆柟寮忥紵\n\nA. 閫氳繃鍏冪礌鐨凜SS绫诲悕瀹氫綅\nB. 閫氳繃鍏冪礌鐨勫唴瀹规弿杩帮紙content-desc锛夋垨accessibilityLabel瀹氫綅\nC. 閫氳繃鍏冪礌鐨勫潗鏍囦綅缃畾浣峔nD. 閫氳繃鍏冪礌鐨勬枃鏈唴瀹瑰畾浣?",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "Appium鑷姩鍖?"
        },
        {
            "title": "Appium娴嬭瘯涓紝'Desired Capabilities'鐨勪綔鐢ㄦ槸浠€涔堬紵",
            "desc": "Appium娴嬭瘯涓紝'Desired Capabilities'鐨勪綔鐢ㄦ槸浠€涔堬紵\n\nA. 鐢ㄤ簬鏂█娴嬭瘯缁撴灉\nB. 鐢ㄤ簬閰嶇疆娴嬭瘯浼氳瘽鐨勭幆澧冨弬鏁帮紝濡傚钩鍙板悕绉般€佽澶囧悕绉般€佸簲鐢ㄨ矾寰勭瓑\nC. 鐢ㄤ簬鐢熸垚娴嬭瘯鎶ュ憡\nD. 鐢ㄤ簬绠＄悊娴嬭瘯鏁版嵁",
            "sol": "B",
            "type": "single_choice",
            "diff": "easy",
            "cat": "Appium鑷姩鍖?"
        },
        {
            "title": "浠ヤ笅鍝鎵嬪娍鎿嶄綔鍦ˋppium涓渶瑕佷娇鐢═ouchAction绫诲疄鐜帮紵",
            "desc": "浠ヤ笅鍝鎵嬪娍鎿嶄綔鍦ˋppium涓渶瑕佷娇鐢═ouchAction绫诲疄鐜帮紵\n\nA. 鐐瑰嚮锛圕lick锛塡nB. 婊戝姩锛圫wipe锛塡nC. 杈撳叆鏂囨湰锛圫end Keys锛塡nD. 鑾峰彇鍏冪礌鏂囨湰锛圙et Text锛?",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "Appium鑷姩鍖?"
        },
        # 鎬ц兘娴嬭瘯涓嶮onkey
        {
            "title": "绉诲姩绔€ц兘娴嬭瘯涓紝'鍐峰惎鍔ㄣ€屽拰銆嶇儹鍚姩'鐨勫尯鍒槸浠€涔堬紵",
            "desc": "绉诲姩绔€ц兘娴嬭瘯涓紝'鍐峰惎鍔ㄣ€屽拰銆嶇儹鍚姩'鐨勫尯鍒槸浠€涔堬紵\n\nA. 鍐峰惎鍔ㄦ槸浠庢闈㈢偣鍑诲浘鏍囧惎鍔紝鐑惎鍔ㄦ槸浠庡悗鍙版仮澶嶅埌鍓嶅彴\nB. 鍐峰惎鍔ㄥ拰鐑惎鍔ㄦ病鏈変换浣曞尯鍒玕nC. 鍐峰惎鍔ㄦ槸绗竴娆″畨瑁呭悗鐨勫惎鍔紝鐑惎鍔ㄦ槸鏇存柊鍚庣殑鍚姩\nD. 鍐峰惎鍔ㄩ渶瑕佽仈缃戯紝鐑惎鍔ㄤ笉闇€瑕佽仈缃?",
            "sol": "A",
            "type": "single_choice",
            "diff": "easy",
            "cat": "鎬ц兘娴嬭瘯"
        },
        {
            "title": "Android Monkey娴嬭瘯宸ュ叿鐨勪富瑕佷綔鐢ㄦ槸浠€涔堬紵",
            "desc": "Android Monkey娴嬭瘯宸ュ叿鐨勪富瑕佷綔鐢ㄦ槸浠€涔堬紵\n\nA. 鑷姩鍖栨墽琛屽姛鑳芥祴璇曠敤渚媆nB. 鍚戠郴缁熷彂閫佷吉闅忔満鐨勭敤鎴蜂簨浠舵祦锛堢偣鍑汇€佽Е鎽搞€佹墜鍔跨瓑锛夛紝鐢ㄤ簬绋冲畾鎬ф祴璇昞nC. 娴嬭瘯搴旂敤鐨勭綉缁滄€ц兘\nD. 鐢熸垚娴嬭瘯鎶ュ憡",
            "sol": "B",
            "type": "single_choice",
            "diff": "easy",
            "cat": "鎬ц兘娴嬭瘯"
        },
        {
            "title": "浠ヤ笅鍝簺鏄Щ鍔ㄧ鎬ц兘娴嬭瘯闇€瑕佸叧娉ㄧ殑鎸囨爣锛?",
            "desc": "浠ヤ笅鍝簺鏄Щ鍔ㄧ鎬ц兘娴嬭瘯闇€瑕佸叧娉ㄧ殑鎸囨爣锛燂紙澶氶€夛級\n\nA. 鍚姩鏃堕棿\nB. 鍐呭瓨鍗犵敤\nC. CPU浣跨敤鐜嘰nD. 鐢甸噺娑堣€?",
            "sol": "A,B,C,D",
            "type": "multiple_choice",
            "diff": "easy",
            "cat": "鎬ц兘娴嬭瘯"
        },
        {
            "title": "浣跨敤Monkey杩涜绋冲畾鎬ф祴璇曟椂锛屼互涓嬪摢涓弬鏁板彲浠ヨ缃簨浠跺彂閫佺殑鏃堕棿闂撮殧锛?",
            "desc": "浣跨敤Monkey杩涜绋冲畾鎬ф祴璇曟椂锛屼互涓嬪摢涓弬鏁板彲浠ヨ缃簨浠跺彂閫佺殑鏃堕棿闂撮殧锛焅n\nA. --throttle\nB. --count\nC. --seed\nD. --ignore-crashes",
            "sol": "A",
            "type": "single_choice",
            "diff": "medium",
            "cat": "鎬ц兘娴嬭瘯"
        },
        {
            "title": "绉诲姩绔€屽唴瀛樻硠婕忋€嶆祴璇曢€氬父浣跨敤浠€涔堝伐鍏疯繘琛岋紵",
            "desc": "绉诲姩绔€屽唴瀛樻硠婕忋€嶆祴璇曢€氬父浣跨敤浠€涔堝伐鍏疯繘琛岋紵\n\nA. Postman\nB. Android Profiler锛圓ndroid锛夊拰 Instruments锛坕OS锛塡nC. Charles\nD. Selenium",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "鎬ц兘娴嬭瘯"
        },
        # 鍒ゆ柇棰?
        {
            "title": "Android鍜宨OS鐨勬帹閫侀€氱煡鏈哄埗瀹屽叏鐩稿悓锛岄兘浣跨敤APNs鏈嶅姟銆?",
            "desc": "Android鍜宨OS鐨勬帹閫侀€氱煡鏈哄埗瀹屽叏鐩稿悓锛岄兘浣跨敤APNs鏈嶅姟銆俓n\nA. 姝ｇ‘\nB. 閿欒",
            "sol": "B",
            "type": "true_false",
            "diff": "easy",
            "cat": "绉诲姩绔祴璇曟杩?"
        },
        {
            "title": "绉诲姩绔簲鐢ㄤ笉闇€瑕佽繘琛屾潈闄愭祴璇曪紝鍥犱负鏉冮檺绠＄悊瀹屽叏鐢辨搷浣滅郴缁熻礋璐ｃ€?",
            "desc": "绉诲姩绔簲鐢ㄤ笉闇€瑕佽繘琛屾潈闄愭祴璇曪紝鍥犱负鏉冮檺绠＄悊瀹屽叏鐢辨搷浣滅郴缁熻礋璐ｃ€俓n\nA. 姝ｇ‘\nB. 閿欒",
            "sol": "B",
            "type": "true_false",
            "diff": "easy",
            "cat": "绉诲姩绔姛鑳芥祴璇?"
        },
        {
            "title": "Appium鍙互鍚屾椂鏀寔Android鍜宨OS骞冲彴鐨勮嚜鍔ㄥ寲娴嬭瘯銆?",
            "desc": "Appium鍙互鍚屾椂鏀寔Android鍜宨OS骞冲彴鐨勮嚜鍔ㄥ寲娴嬭瘯銆俓n\nA. 姝ｇ‘\nB. 閿欒",
            "sol": "A",
            "type": "true_false",
            "diff": "easy",
            "cat": "Appium鑷姩鍖?"
        },
        {
            "title": "Android纰庣墖鍖栭棶棰樻瘮iOS鏇翠弗閲嶏紝鍥犱负Android璁惧鍜岀郴缁熺増鏈洿澶氭牱鍖栥€?",
            "desc": "Android纰庣墖鍖栭棶棰樻瘮iOS鏇翠弗閲嶏紝鍥犱负Android璁惧鍜岀郴缁熺増鏈洿澶氭牱鍖栥€俓n\nA. 姝ｇ‘\nB. 閿欒",
            "sol": "A",
            "type": "true_false",
            "diff": "easy",
            "cat": "鍏煎鎬ф祴璇?"
        },
        {
            "title": "Charles Proxy鍙兘鐢ㄤ簬Web璋冭瘯锛屼笉鑳界敤浜庣Щ鍔ㄧ寮辩綉妯℃嫙銆?",
            "desc": "Charles Proxy鍙兘鐢ㄤ簬Web璋冭瘯锛屼笉鑳界敤浜庣Щ鍔ㄧ寮辩綉妯℃嫙銆俓n\nA. 姝ｇ‘\nB. 閿欒",
            "sol": "B",
            "type": "true_false",
            "diff": "easy",
            "cat": "寮辩綉娴嬭瘯"
        },
        # 鏇村鍗曢€夐
        {
            "title": "绉诲姩绔祴璇曚腑锛?涓柇娴嬭瘯'涓昏娴嬭瘯浠€涔堝満鏅紵",
            "desc": "绉诲姩绔祴璇曚腑锛?涓柇娴嬭瘯'涓昏娴嬭瘯浠€涔堝満鏅紵\n\nA. 搴旂敤杩愯杩囩▼涓鏉ョ數銆佺煭淇°€侀€氱煡銆侀椆閽熺瓑鎵撴柇鍚庣殑琛ㄧ幇\nB. 缃戠粶涓柇鍚庣殑鎭㈠鑳藉姏\nC. 鏈嶅姟鍣ㄤ腑鏂悗鐨勫閿欏鐞哱nD. 鐢ㄦ埛鎿嶄綔涓柇鐨勫搷搴旈€熷害",
            "sol": "A",
            "type": "single_choice",
            "diff": "easy",
            "cat": "绉诲姩绔姛鑳芥祴璇?"
        },
        {
            "title": "浠ヤ笅鍝釜涓嶆槸甯歌鐨勭Щ鍔ㄧ涓撻」娴嬭瘯绫诲瀷锛?",
            "desc": "浠ヤ笅鍝釜涓嶆槸甯歌鐨勭Щ鍔ㄧ涓撻」娴嬭瘯绫诲瀷锛焅n\nA. 瀹夎/鍗歌浇/鍗囩骇娴嬭瘯\nB. 鏉冮檺娴嬭瘯\nC. 鏁版嵁搴撴€ц兘娴嬭瘯\nD. 鎺ㄩ€侀€氱煡娴嬭瘯",
            "sol": "C",
            "type": "single_choice",
            "diff": "easy",
            "cat": "绉诲姩绔姛鑳芥祴璇?"
        },
        {
            "title": "鍦ㄧЩ鍔ㄧUI娴嬭瘯涓紝涓轰粈涔堥渶瑕佹祴璇?娣辫壊妯″紡'锛?",
            "desc": "鍦ㄧЩ鍔ㄧUI娴嬭瘯涓紝涓轰粈涔堥渶瑕佹祴璇?娣辫壊妯″紡'锛焅n\nA. 娣辫壊妯″紡鍙槸瑙嗚鏁堟灉锛屼笉闇€瑕佹祴璇昞nB. 闇€瑕佺‘淇濇枃瀛楀姣斿害銆佸浘鏍囨樉绀恒€佸浘鐗囬€傞厤绛夊湪娣辫壊妯″紡涓嬫甯竆nC. 鍙湁iOS鏀寔娣辫壊妯″紡锛孉ndroid涓嶉渶瑕佹祴璇昞nD. 娣辫壊妯″紡鏄郴缁熷姛鑳斤紝搴旂敤涓嶉渶瑕侀€傞厤",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "鍏煎鎬ф祴璇?"
        },
        {
            "title": "绉诲姩绔€岀數閲忔祴璇曘€嶄富瑕佸叧娉ㄤ粈涔堬紵",
            "desc": "绉诲姩绔€岀數閲忔祴璇曘€嶄富瑕佸叧娉ㄤ粈涔堬紵\n\nA. 搴旂敤鍦ㄤ笉鍚屼娇鐢ㄥ満鏅笅鐨勭數閲忔秷鑰楁儏鍐礬nB. 鍏呯數閫熷害\nC. 鐢垫睜瀹归噺澶у皬\nD. 鍏呯數鍣ㄥ姛鐜?",
            "sol": "A",
            "type": "single_choice",
            "diff": "medium",
            "cat": "鎬ц兘娴嬭瘯"
        },
        {
            "title": "鍦ˋppium娴嬭瘯涓紝閬囧埌銆屽厓绱犲畾浣嶄笉鍒般€嶇殑闂锛屽彲鑳界殑瑙ｅ喅鏂规硶鏈夊摢浜涳紵",
            "desc": "鍦ˋppium娴嬭瘯涓紝閬囧埌銆屽厓绱犲畾浣嶄笉鍒般€嶇殑闂锛屽彲鑳界殑瑙ｅ喅鏂规硶鏈夊摢浜涳紵锛堝閫夛級\n\nA. 娣诲姞鏄惧紡绛夊緟锛圗xplicit Wait锛塡nB. 鍒囨崲涓嶅悓鐨勫畾浣嶇瓥鐣ワ紙XPath銆両D銆丄ccessibility ID绛夛級\nC. 妫€鏌ュ厓绱犳槸鍚﹀湪WebView涓紝闇€瑕佸垏鎹笂涓嬫枃\nD. 鐩存帴澧炲姞鍥哄畾鐨剆leep绛夊緟",
            "sol": "A,B,C",
            "type": "multiple_choice",
            "diff": "medium",
            "cat": "Appium鑷姩鍖?"
        },
        {
            "title": "绉诲姩绔祴璇曚腑鐨勩€岀敤鎴蜂綋楠屾祴璇曘€嶅寘鍚摢浜涚淮搴︼紵",
            "desc": "绉诲姩绔祴璇曚腑鐨勩€岀敤鎴蜂綋楠屾祴璇曘€嶅寘鍚摢浜涚淮搴︼紵锛堝閫夛級\n\nA. 鐣岄潰缇庤搴nB. 浜や簰娴佺晠搴nC. 鎿嶄綔鍙嶉鍙婃椂鎬nD. 閿欒鎻愮ず鍙嬪ソ搴?",
            "sol": "A,B,C,D",
            "type": "multiple_choice",
            "diff": "easy",
            "cat": "绉诲姩绔姛鑳芥祴璇?"
        },
        {
            "title": "浠ヤ笅鍏充簬绉诲姩绔祴璇曞拰Web绔祴璇曞尯鍒殑鎻忚堪锛屾纭殑鏄紵",
            "desc": "浠ヤ笅鍏充簬绉诲姩绔祴璇曞拰Web绔祴璇曞尯鍒殑鎻忚堪锛屾纭殑鏄紵\n\nA. 绉诲姩绔祴璇曞拰Web绔祴璇曞畬鍏ㄧ浉鍚岋紝娌℃湁鍖哄埆\nB. 绉诲姩绔祴璇曢渶瑕佽€冭檻鏇村璁惧鍜岀幆澧冨洜绱狅紝濡傜數閲忋€佷俊鍙枫€佷紶鎰熷櫒绛塡nC. Web绔祴璇曟瘮绉诲姩绔祴璇曟洿澶嶆潅\nD. 绉诲姩绔笉闇€瑕佽繘琛屽姛鑳芥祴璇曪紝鍙渶瑕佸仛鍏煎鎬ф祴璇?",
            "sol": "B",
            "type": "single_choice",
            "diff": "easy",
            "cat": "绉诲姩绔祴璇曟杩?"
        },
        {
            "title": "鍦ㄨ繘琛岀Щ鍔ㄧ銆屾í绔栧睆鍒囨崲銆嶆祴璇曟椂锛屽簲璇ュ叧娉ㄤ粈涔堬紵",
            "desc": "鍦ㄨ繘琛岀Щ鍔ㄧ銆屾í绔栧睆鍒囨崲銆嶆祴璇曟椂锛屽簲璇ュ叧娉ㄤ粈涔堬紵\n\nA. 鐣岄潰甯冨眬鏄惁姝ｇ‘閫傞厤锛屾暟鎹槸鍚︿涪澶憋紝鐘舵€佹槸鍚︿繚鎸乗nB. 鍙渶瑕佹祴璇曚粠绔栧睆鍒囧埌妯睆\nC. 妯珫灞忓垏鎹笉闇€瑕佹祴璇曪紝鐢ㄦ埛寰堝皯鐢╘nD. 鍙渶瑕佹鏌ョ晫闈㈡槸鍚︽棆杞嵆鍙?",
            "sol": "A",
            "type": "single_choice",
            "diff": "medium",
            "cat": "绉诲姩绔姛鑳芥祴璇?"
        },
        {
            "title": "绉诲姩绔€屽畨鍏ㄦ祴璇曘€嶇浉姣擶eb绔紝鏈夊摢浜涚壒娈婂叧娉ㄧ偣锛?",
            "desc": "绉诲姩绔€屽畨鍏ㄦ祴璇曘€嶇浉姣擶eb绔紝鏈夊摢浜涚壒娈婂叧娉ㄧ偣锛焅n\nA. 涓嶉渶瑕佸叧娉ㄥ畨鍏ㄩ棶棰榎nB. 闇€瑕佸叧娉ㄦ湰鍦版暟鎹瓨鍌ㄥ畨鍏ㄣ€佽瘉涔?pinning銆佸弽缂栬瘧闃叉姢绛塡nC. 鍙渶瑕佸叧娉ㄧ綉缁滀紶杈撳畨鍏╘nD. 绉诲姩绔畨鍏ㄦ祴璇曞拰Web绔畬鍏ㄧ浉鍚?",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "绉诲姩绔祴璇曟杩?"
        },
        {
            "title": "Monkey娴嬭瘯涓殑'--ignore-crashes'鍙傛暟鐨勪綔鐢ㄦ槸浠€涔堬紵",
            "desc": "Monkey娴嬭瘯涓殑'--ignore-crashes'鍙傛暟鐨勪綔鐢ㄦ槸浠€涔堬紵\n\nA. 蹇界暐鎵€鏈夊紓甯革紝缁х画鍙戦€佷簨浠禱nB. 閬囧埌搴旂敤宕╂簝鏃朵笉鍋滄娴嬭瘯锛岀户缁彂閫佷簨浠禱nC. 蹇界暐ANR閿欒\nD. 涓嶇敓鎴愬穿婧冩棩蹇?",
            "sol": "B",
            "type": "single_choice",
            "diff": "medium",
            "cat": "鎬ц兘娴嬭瘯"
        },
        {
            "title": "浠ヤ笅鍝釜鍛戒护鍙互鍚姩Android Monkey娴嬭瘯锛屽彂閫?000涓殢鏈轰簨浠讹紵",
            "desc": "浠ヤ笅鍝釜鍛戒护鍙互鍚姩Android Monkey娴嬭瘯锛屽彂閫?000涓殢鏈轰簨浠讹紵\n\nA. adb shell monkey -p com.example.app 1000\nB. adb shell monkey com.example.app 1000\nC. monkey -p com.example.app 1000\nD. adb monkey -p com.example.app 1000",
            "sol": "A",
            "type": "single_choice",
            "diff": "easy",
            "cat": "鎬ц兘娴嬭瘯"
        },
    ]
    return exercises


# ============== 涓诲嚱鏁?==============
if __name__ == '__main__':
    print("=" * 60)
    print("?????? LP12-LP18 ?????")
    print("=" * 60)

    conn = get_db()
    cursor = conn.cursor()

    # 鍒犻櫎LP12-LP18鐨勫瀮鍦鹃鐩?
    for lp_id in range(12, 19):
        deleted = delete_bad_exercises(lp_id)
        print(f"\nLP{lp_id}: ??? {deleted} ?????")

    # 鐢熸垚LP12棰樼洰
    print("\n--- ?? LP12????????????? ---")
    lp12_exercises = generate_lp12_exercises(cursor)
    lp12_id = 12
    for ex in lp12_exercises:
        insert_exercise(cursor, ex['title'], ex['desc'], ex['sol'], ex['type'], ex['diff'], lp12_id, ex['cat'])
    print(f"LP12: ??? {len(lp12_exercises)} ???")

    conn.commit()
    conn.close()
    print("\nLP12 ????")

