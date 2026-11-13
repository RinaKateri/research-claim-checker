# A first look at Laminar: from tracing an agent to testing its answers

*Getting an agent to return an answer is one milestone. Understanding whether you can trust that answer is the next.*

[Agent code](https://github.com/RinaKateri/research-claim-checker)

I explored Laminar with a small research claim checker. Given a paper ID and a claim, it retrieves a fictional abstract through `lookup_paper` and returns `supported`, `contradicted`, or `insufficient_evidence`, with an explanation.

The agent is deliberately simple. It still produced a useful failure: it retrieved the right evidence, completed without errors, and returned the wrong verdict.

## What Laminar gives you

Laminar is an open-source platform that connects **what your agent did, what it cost, and whether its answer held up**. Traces expose model calls and tool results alongside latency and token usage. Signals analyze runs for behaviors you define, including failures that don't throw exceptions. Evaluations score outputs against explicit expectations.

I used that workflow to investigate a wrong verdict from this claim checker.

## Run the example

The implementation was tested on macOS with Python 3.14.6, OpenAI SDK 2.54.0, `python-dotenv` 1.2.4, and Laminar SDK 0.8.10. These are the observed versions, not a fully locked environment.

```sh
git clone https://github.com/RinaKateri/research-claim-checker.git
cd research-claim-checker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Create a Laminar project and generate a project API key in its settings. Configure your local `.env`:

```text
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4.1-mini
LMNR_PROJECT_API_KEY=your-laminar-project-key
```

Model requests use OpenAI credits; Signal analysis has separate Laminar usage charges. Claims and retrieved abstracts are sent to OpenAI, and captured trace content is sent to Laminar.

## 1. Get a trace you can follow

The agent makes two model requests and one local tool call:

```text
claim_check
├── openai.chat: requests lookup_paper
├── lookup_paper: returns the fictional abstract
└── openai.chat: returns the verdict and explanation
```

The application requires the lookup through `tool_choice`; the model supplies the arguments.

Following the Python OpenAI integration, I loaded `.env` and initialized Laminar before creating the OpenAI client. Automatic instrumentation captured the model requests. I added:

```python
@observe(name="claim_check")
```

to the agent function and:

```python
@observe(name="lookup_paper", span_type="TOOL")
```

to the local lookup. The parent span connects both model requests and the local lookup in one trace. The CLI also flushes pending telemetry before exiting.

Run the first claim:

```sh
python claim_checker.py fictional-webcam-001 "The method was tested on seated participants"
```

Expect a tool-call line and a `supported` verdict. In Laminar, open **Traces**, select `claim_check`, and inspect the `lookup_paper` span's input and output.

![The retrieved abstract beside the agent transcript](docs/images/trace-evidence.png)

The tool output showed the evidence used by the final model request: a fictional study of 24 seated adults under stable indoor lighting.

One inspected run took 2.97 seconds, used 462 tokens, and had a reported model cost of $0.00024. The local lookup took about 3 milliseconds; model requests accounted for nearly all elapsed time.

### What the trace revealed

Next, I tried:

```sh
python claim_checker.py fictional-webcam-001 "The method accurately estimates heart rate during exercise"
```

The abstract explicitly says exercise conditions were not evaluated. That establishes neither success nor failure during exercise, so the expected verdict is `insufficient_evidence`.

One traced run returned `contradicted`.

Inspecting the trace showed that retrieval worked and the final model request received the correct abstract. The error was in classifying the evidence, rather than finding or passing it along.

**A green trace indicated successful execution—not a correct answer.** The verdict varied across runs, so you may not reproduce the error on your next attempt.
