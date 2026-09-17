# SGLang 架构图集

按 [`sgl-project/sglang`](https://github.com/sgl-project/sglang) `@ bdf8886ad386685b4d089c8e66725b9280533591` 源码绘制的交互式架构图。在线打开即可用（深/浅色、搜索、路径探测、PNG/SVG 导出）。

**目录页：https://sunsh-ine.github.io/SGlang/**

## 整体框架

| 图 | 在线地址 | 源码依据 |
|---|---|---|
| SGLang 运行时架构 | https://sunsh-ine.github.io/SGlang/overview/sglang-runtime-architecture.html | `launch_server.py`、`entrypoints/http_server.py`、`managers/{tokenizer_manager,scheduler,detokenizer_manager,tp_worker}.py`、`mem_cache/{memory_pool,unified_radix_cache}.py` |

## 组件图

| 图 | 在线地址 | 源码依据 |
|---|---|---|
| Scheduler 调度主循环 | https://sunsh-ine.github.io/SGlang/components/sglang-scheduler-loop.html | `managers/scheduler.py`（`event_loop_normal:1906`、`get_next_batch_to_run:3508`、`run_batch:4210`、`process_batch_result:4559`、`schedule_policy.py`） |
| Scheduler 同步 / Overlap：CPU–GPU 时间线 | https://sunsh-ine.github.io/SGlang/components/sglang-scheduler-cpu-gpu-timeline.html | 同上两个事件循环；`copy_done.synchronize` 见 `scheduler_components/batch_result_processor.py` |
| 请求往返：请求下行与 token 回流 | https://sunsh-ine.github.io/SGlang/components/sglang-request-roundtrip.html | `http_server.py:911`、`tokenizer_manager.py:776/2252`、`scheduler.py:1906`、`tp_worker.py:593/672`、`detokenizer_manager.py:179/443` |
| TokenizerManager：进来、下发、回包 | https://sunsh-ine.github.io/SGlang/components/sglang-tokenizer-manager.html | `tokenizer_manager.py`（`generate_request:776`、`_init_req_state`、`_tokenize_one_request`、`_dispatch_to_scheduler:577`、`handle_loop:2237`、`_handle_batch_output:2252`） |
| DetokenizerManager：ids → 文本 → 归位 | https://sunsh-ine.github.io/SGlang/components/sglang-detokenizer-manager.html | `detokenizer_manager.py`（`init_ipc_channels:121`、`event_loop:179`、`_decode_batch_token_id_output:303`、`handle_batch_token_id_out:443`） |
| TpModelWorker：一次前向的打包、执行、回传 | https://sunsh-ine.github.io/SGlang/components/sglang-tp-model-worker.html | `tp_worker.py:593/672`、`forward_batch_info.py:759`、`model_executor/model_runner.py:1628/1805/1900`、`layers/communicator.py:518`、`layers/logits_processor.py:421` |

## 文件说明

```
index.html                                  目录页（GitHub Pages 入口）
overview/sglang-runtime-architecture.html   整体架构
components/*.html                           组件图（每张都是自包含 HTML，可离线打开）
components/*.json                           Archify 的 typed JSON 源，改一处即可重新渲染
components/sglang-scheduler-cpu-gpu-timeline.generate.py
                                            时间线图的生成脚本（纯标准库，改数据后重跑）
```

重新生成 Archify 图（需要 [Archify](https://github.com/tt-a1i/archify)）：

```bash
node bin/archify.mjs deliver workflow components/sglang-scheduler-loop.json /tmp/out.html --quality showcase
```

图表中的刻度、编号均为示意值，用于说明数据流与组件关系；行为以代码为准。
