# Demo 用硬编码数据，避免每次 Demo 都调 AI 解析
DEMO_NOVEL_ID = "1725479677609644032"

DEMO_CHARACTERS = [
    {
        "id": "wentang",
        "name": "温棠",
        "role": "protagonist",
        "personality": ["温和隐忍", "善良心软", "重亲情"],
        "skills": ["枣花糕", "针线活", "倾听"],
        "initial_intimacy": 50,
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
        "initial_intimacy": 40,
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
