# Prompt length in each model's own tokens

Documents are sized in Llama 3.1 tokens. Numbers are the longest normal prompt at each length (+320 for the answer must fit the window).

| model | window | 8K prompt | 32K prompt | 64K prompt | 128K prompt | fits 128K? | PC limit |
|---|---|---|---|---|---|---|---|
| llama31_8b | 131,072 | 8,111 (1.00x) | 32,106 (1.00x) | 64,100 (1.00x) | 128,078 (1.00x) | yes | 34,816 ok for 32K |
| qwen3_4b | 262,144 | 9,754 (1.20x) | 38,680 (1.20x) | 77,806 (1.21x) | 155,203 (1.21x) | yes | 40,960 ok for 32K |
| gemma3_27b | 131,072 | 9,817 (1.21x) | 38,841 (1.21x) | 78,143 (1.22x) | 155,929 (1.22x) **TOO LONG** | **no** |  |
| qwen3_30b_a3b | 262,144 | 9,754 (1.20x) | 38,680 (1.20x) | 77,806 (1.21x) | 155,203 (1.21x) | yes |  |
| llama33_70b | 131,072 | 8,111 (1.00x) | 32,106 (1.00x) | 64,100 (1.00x) | 128,078 (1.00x) | yes |  |
| qwen3_next_80b | 262,144 | 9,754 (1.20x) | 38,680 (1.20x) | 77,806 (1.21x) | 155,203 (1.21x) | yes |  |
| glm45_air | 131,072 | 8,375 (1.03x) | 33,221 (1.03x) | 66,459 (1.04x) | 132,771 (1.04x) **TOO LONG** | **no** |  |

## Problems

- gemma3_27b: 128K needs 156,249 tokens, window is 131,072
- glm45_air: 128K needs 133,091 tokens, window is 131,072
