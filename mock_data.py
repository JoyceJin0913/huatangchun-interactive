# Demo 用硬编码数据，避免每次 Demo 都调 AI 解析
DEMO_NOVEL_ID = "1725479677609644032"

DEMO_CHARACTERS = [
    {
        "id": "wentang",
        "name": "温棠",
        "role": "protagonist",
        "personality": ["温和隐忍", "善良心软", "重亲情"],
        "skills": ["枣花糕", "针线活", "倾听"],
        "initial_intimacy": 50,  # 主角自身，不计入亲密度追踪
    },
    {
        "id": "peirong",
        "name": "裴容",
        "role": "emperor",
        "personality": ["理性凉薄", "喜怒不形于色", "看重安分"],
        "skills": ["权衡利弊", "识人精准"],
        "initial_intimacy": 30,
    },
    {
        "id": "peiyan",
        "name": "裴琰",
        "role": "prince",
        "personality": ["早熟隐忍", "知恩图报", "察言观色"],
        "skills": ["揣摩人心", "乖巧懂事"],
        "initial_intimacy": 50,
    },
    {
        "id": "peiyu",
        "name": "裴瑜",
        "role": "rival_son",
        "personality": ["骄纵傲慢", "趋炎附势"],
        "skills": ["撒娇争宠"],
        "initial_intimacy": 20,
    },
]

DEMO_ACTS = [
    {
        "act_id": 1,
        "title": "雪夜承宠",
        "content_html": "<p>温棠入宫十年，无宠无位，采桑宫一隅，岁月静默流逝。雪夜，皇帝驾临，偶遇温棠为裴琰缝补衣物……</p>",
        "nodes": [
            {
                "node_id": "act1_node1",
                "type": "single_choice",
                "trigger": "裴容询问后",
                "prompt": "裴容放下书卷，沉声道：「朕问你，想不想抚育三皇子琰儿？」",
                # 兼容旧逻辑的默认选项（温棠视角）
                "options": [
                    {
                        "id": "A",
                        "text": "欣然应允：「臣妾愿悉心照料琰儿」",
                        "intimacy_delta": {"peiyan": 15, "peirong": 10},
                    },
                    {
                        "id": "B",
                        "text": "犹豫试探：「陛下，琰儿乃皇子，臣妾恐难当此任」",
                        "intimacy_delta": {"peiyan": 5, "peirong": 5},
                    },
                    {
                        "id": "C",
                        "text": "婉言拒绝：「臣妾只想盼着瑜儿回心转意」",
                        "intimacy_delta": {"peirong": -5, "peiyu": 5},
                    },
                ],
                # 按角色区分的选项
                "options_by_char": {
                    "wentang": [
                        {
                            "id": "A",
                            "text": "欣然应允：「臣妾愿悉心照料琰儿，视若己出」",
                            "intimacy_delta": {"peiyan": 15, "peirong": 10},
                        },
                        {
                            "id": "B",
                            "text": "犹豫试探：「陛下，琰儿乃皇子，臣妾恐难当此任……」",
                            "intimacy_delta": {"peiyan": 5, "peirong": 5},
                        },
                        {
                            "id": "C",
                            "text": "婉言拒绝：「臣妾只想盼着瑜儿有朝一日回心转意」",
                            "intimacy_delta": {"peirong": -5, "peiyu": 5},
                        },
                    ],
                    "peiyan": [
                        {
                            "id": "A",
                            "text": "默然观察：我只需看清父皇此举究竟是试探还是安排",
                            "intimacy_delta": {"wentang": 0, "peirong": 5},
                        },
                        {
                            "id": "B",
                            "text": "乖巧应声：「儿臣谢父皇，定不叫娘娘为难」",
                            "intimacy_delta": {"wentang": 10, "peirong": 8},
                        },
                        {
                            "id": "C",
                            "text": "试探温棠：悄悄退后半步，等着看她是欢喜还是为难",
                            "intimacy_delta": {"wentang": 5, "peirong": 3},
                        },
                    ],
                },
            },
            {
                "node_id": "act1_node2",
                "type": "free_input",
                "trigger": "裴琰独处时",
                "prompt": "裴琰望着你，轻声问道：「娘娘，您真的愿意留下琰儿吗？」",
                "options": [],
            },
        ],
    },
    {
        "act_id": 2,
        "title": "抚育之诺",
        "content_html": "<p>圣旨下达，裴琰正式入住采桑宫。温棠为他缝冬衣、做枣花糕，两人渐生母子情……</p>",
        "nodes": [
            {
                "node_id": "act2_node1",
                "type": "single_choice",
                "trigger": "裴琰入宫后",
                "prompt": "裴琰站在门口，你想先做什么？",
                # 默认选项（温棠视角）
                "options": [
                    {
                        "id": "A",
                        "text": "给裴琰做枣花糕",
                        "intimacy_delta": {"peiyan": 20},
                    },
                    {
                        "id": "B",
                        "text": "为裴琰缝补冬衣",
                        "intimacy_delta": {"peiyan": 15},
                    },
                ],
                # 按角色区分的选项
                "options_by_char": {
                    "wentang": [
                        {
                            "id": "A",
                            "text": "亲手做枣花糕：将热腾腾的糕点摆在他面前",
                            "intimacy_delta": {"peiyan": 20},
                        },
                        {
                            "id": "B",
                            "text": "取针线缝补冬衣：让他知道这里有人在乎他",
                            "intimacy_delta": {"peiyan": 15},
                        },
                        {
                            "id": "C",
                            "text": "问他爱吃什么：先了解他，再慢慢走近",
                            "intimacy_delta": {"peiyan": 10, "peirong": 3},
                        },
                    ],
                    "peiyan": [
                        {
                            "id": "A",
                            "text": "主动搭手帮忙：「我来帮娘娘，娘娘别累着」",
                            "intimacy_delta": {"wentang": 18},
                        },
                        {
                            "id": "B",
                            "text": "安静坐在一旁看她做事，记住她的每一个习惯",
                            "intimacy_delta": {"wentang": 12},
                        },
                        {
                            "id": "C",
                            "text": "故意打翻东西，看她如何应对——是恼还是疼",
                            "intimacy_delta": {"wentang": 8},
                        },
                    ],
                },
            }
        ],
    },
    {
        "act_id": 3,
        "title": "帝临采桑",
        "content_html": "<p>裴容驾临采桑宫，见温棠与裴琰相处融洽，问及红豆甜汤……封妃之兆渐显。</p>",
        "nodes": [
            {
                "node_id": "act3_node1",
                "type": "free_input",
                "trigger": "裴容提问后",
                "prompt": "裴容看着你，缓声问道：「你在宫中这些年，可曾后悔过？」",
                "options": [],
            }
        ],
    },
]

DEMO_ROOM_ID = "demo_room_001"
DEMO_INITIAL_INTIMACY = {"peiyan": 50, "peirong": 30, "peiyu": 20}
