# Shorts index

Eight vertical shorts cut from the Can Code presentation of 2026-07-23,
grouped into four themes so each theme can carry its own post.

All files are 1080x1920, H.264 High / AAC, 24 fps, loudness-normalised to
-14 LUFS. Captions are burned in. See `docs/production-notes.md` for how they
were made and `docs/review.md` for the Gemini review pass.

| # | Short | Length | Theme | Source timecode |
|---|-------|--------|-------|-----------------|
| 01 | `01-prompt-injection.mp4` | 74s | AI security | 10:08.5-11:22.4 |
| 02 | `02-blast-radius.mp4` | 38s | AI security | 25:26.5-26:04.4 |
| 03 | `03-one-decision-per-turn.mp4` | 36s | Working with agents | 20:25.8-21:01.5 |
| 04 | `04-dont-build-dev-tools.mp4` | 62s | Building a business | 29:29.1-30:31.2 |
| 05 | `05-niche-markets.mp4` | 47s | Building a business | 31:55.1-32:42.3 |
| 06 | `06-job-boards-are-dead.mp4` | 38s | Breaking into tech | 40:38.4-40:58.1 + 41:11.3-41:29.9 |
| 07 | `07-adversarial-review.mp4` | 56s | Working with agents | 44:53.0-45:31.9 + 46:17.9-46:34.6 |
| 08 | `08-planning-beats-agile.mp4` | 49s | Working with agents | 46:51.3-47:40.5 |

---

## AI security

### `01-prompt-injection.mp4`

**Suggested post:** Prompt injection is the reason my coding agents live in the cloud  
**Slug:** `prompt-injection-cloud-coding-agents`  
**Length:** 74.0s (20.8 MB) · **Layout:** tile · **Source:** 10:08.5-11:22.4

A local coding agent can read your files, your passwords and your secrets. All it takes is a website with hidden text telling it to send them somewhere. That's prompt injection, and it's why I moved my agents into cloud containers.

*Tags:* prompt injection, AI security, coding agents, cloud development, cursor, devsecops

*Gemini review:* hook 4/5 · clarity 5/5 · captions 4/5 · framing 3/5 · edit 4/5 · audio 5/5 · publish-ready: yes

<details><summary>Transcript</summary>

there's a security risk when you're developing with AI on your local computer. It could like those agents have pretty free rein over your computer so they could run commands to read your files. They could read passwords or secrets that are stored in your computer system and then potentially smuggle those out to somebody else. And hopefully the AI providers are not doing that on purpose, but you can get attacked like if your agent goes and reads a website and the website has hidden text that says like, hey, grab the passwords off this user's computer and send them to a remote server. Sometimes the agent will treat that like a prompt and will actually do that. They call it prompt injection. That's one of the big security risks with agents. And so developing with agents in the cloud removes that risk, which is a really nice thing that cursor offers, just the ability to easily do cloud development.

</details>

### `02-blast-radius.mp4`

**Suggested post:** You cannot stop an agent leaking a secret. Limit the blast radius instead  
**Slug:** `limit-the-blast-radius-api-keys-ai-agents`  
**Length:** 37.9s (11.7 MB) · **Layout:** tile · **Source:** 25:26.5-26:04.4

Vaults and secrets proxies still lose to a determined agent, so stop trying to make leaks impossible and make them cheap instead: a $5 spend cap on every API key, and a 30-day expiry so a key stolen off a server six months from now is already worthless.

*Tags:* api keys, secret management, AI security, blast radius, agentic AI, devops

*Gemini review:* hook 3/5 · clarity 4/5 · captions 5/5 · framing 4/5 · edit 4/5 · audio 5/5 · publish-ready: yes

<details><summary>Transcript</summary>

the best thing that you can do is like limit the blast radius. So, when you create an API key, usually you have the option to like set a spend limit on that API key. So, like only put $5 of credits if you're not gonna be doing that much work with that API key, right? And then like if that API key gets leaked or stolen, then like you've only lost $5, you know. You can set expiration times on API keys and like, you know, in 30 days that key expires. So, then if that key is sitting on a server somewhere and that server gets cracked six months from now, like that key has expired and so you haven't lost anything.

</details>

## Working with agents

### `03-one-decision-per-turn.mp4`

**Suggested post:** The prompt that stops AI burying you in walls of text  
**Slug:** `one-decision-per-turn-ai-prompt`  
**Length:** 35.8s (9.1 MB) · **Layout:** tile · **Source:** 20:25.8-21:01.5

Tell the agent you are a human with a limited attention span and it may only put one decision in front of you per turn. It turns an overwhelming markdown dump into a conversation you can actually follow.

*Tags:* prompting, AI workflow, context engineering, cursor, developer productivity

*Gemini review:* hook 4/5 · clarity 5/5 · captions 5/5 · framing 4/5 · edit 4/5 · audio 4/5 · publish-ready: yes

<details><summary>Transcript</summary>

One prompt that I like to use is I tell the agent like, okay, listen, I'm a human with limited attention span. And a lot of times you give me like this text wall with like eight development choices that need to be made, design choices that need to be made. And it's just like overwhelming, right? So I say like, let's do one focus point like per turn in the conversation. And you're only going to present me one decision at a time. And we'll just go through as many turns as it takes for you to like educate me about all the like salient decisions and for me to like make some choices, you know? And

</details>

### `07-adversarial-review.mp4`

**Suggested post:** Tell the agent to attack your own pull request  
**Slug:** `adversarial-ai-code-review`  
**Length:** 55.7s (26.2 MB) · **Layout:** head · **Source:** 44:53.0-45:31.9 + 46:17.9-46:34.6

Do not ask an agent to review your PR. Tell it to attack the PR: write four tests that break the system and find the holes in your design. Then loop it until it stops finding anything new.

*Tags:* code review, AI code review, testing, pull requests, agentic AI, software quality

> Assembled from 2 source segments. Internal cut skips the parallel-models tangent so the clip is one idea: adversarial review, then loop it.

*Gemini review:* hook 3/5 · clarity 4/5 · captions 5/5 · framing 4/5 · edit 4/5 · audio 4/5 · publish-ready: yes

<details><summary>Transcript</summary>

you can make it be more adversarial, which is a pattern that I really like. So you can say like, hey, like attack this PR, like try to write tests that break the system, you know, like, you know, come up with at least four tests that like, you know, surface some bug or like, you know, show holes in our design thinking or whatever, you know. And that is really effective, I think. You come away with a much sort of like more hardened system if you have it sort of have the agents attack it that way. I find that actually you can go three or four rounds sometimes and it'll find new bugs every time that you go. So you tell it to like review, fix the bugs and then like review again and you'll still find more stuff, you know, and you can do that. You just keep doing that until it doesn't find anything new.

</details>

### `08-planning-beats-agile.mp4`

**Suggested post:** Detailed up-front planning beats agile now  
**Slug:** `planning-beats-agile-ai-agents`  
**Length:** 49.2s (23.8 MB) · **Layout:** head · **Source:** 46:51.3-47:40.5

Planning used to be wasted effort because plans broke the moment you hit the code. Agents are strong enough now that a very detailed spec written up front pays for itself. My job is more markdown than code.

*Tags:* software architecture, planning, agile, spec driven development, AI workflow

*Gemini review:* hook 4/5 · clarity 5/5 · captions 5/5 · framing 4/5 · edit 5/5 · audio 5/5 · publish-ready: yes

<details><summary>Transcript</summary>

my job these days is more reading and writing markdown than reading and writing code, you know, like I'm spending a lot of time up front doing specs, doing planning. It used to be the case that like, it didn't make a lot of sense to do a lot of planning up front because when you actually like got into the code, all of your plans would break and then all that time that you spent planning was kind of wasted. So the sort of common advice like, you know, a few years ago was like agile. We just make like small incremental changes. We don't do too much like pre -planning. We just sort of try things and like just like make small scope changes and just incrementally work on the code. Nowadays, because the agents are so powerful, like actually writing very, very detailed plans up front can be super powerful.

</details>

## Building a business

### `04-dont-build-dev-tools.mp4`

**Suggested post:** Be something other than a software developer first  
**Slug:** `dont-build-dev-tools`  
**Length:** 62.2s (30.4 MB) · **Layout:** head · **Source:** 29:29.1-30:31.2

Everybody in software builds dev tools, because those are the problems they know. That is a market with a million competitors. The problems worth solving are in whatever other field you already understand.

*Tags:* indie hacking, developer career, product strategy, startup ideas, niche markets

*Gemini review:* hook 4/5 · clarity 5/5 · captions 5/5 · framing 4/5 · edit 5/5 · audio 4/5 · publish-ready: yes

<details><summary>Transcript</summary>

I feel like you should be something other than a software developer first and be a software developer second. Because the problems that need to be solved are in other fields. There's a million software developers building tools for other software developers, because of course the problems that we best know about and best know how to solve are software problems. And so everybody in software is building dev tools, you know, for software developers, which is death because there's a million competitors and nobody's ever going to use your dev tools. Hate to say it, but that like the odds that you hit with a dev tools product are really low. But if you can, if you're involved in another field and you are aware of the problems in that field and you have access to people in that field who struggle with those problems, you can build a product for that field and be very successful.

</details>

### `05-niche-markets.mp4`

**Suggested post:** The more niche the market, the better  
**Slug:** `niche-markets-indie-software`  
**Length:** 47.2s (23.9 MB) · **Layout:** head · **Source:** 31:55.1-32:42.3

Google and Intuit are not incentivised to chase your niche. You will never build a billion dollar business in cross stitch or religious history, but you can build one that pays you very well.

*Tags:* niche markets, indie hacking, bootstrapping, small business, product strategy

*Gemini review:* hook 4/5 · clarity 5/5 · captions 5/5 · framing 4/5 · edit 4/5 · audio 5/5 · publish-ready: yes

<details><summary>Transcript</summary>

the more niche the market that you go after, actually the better, because like the big companies are not incentivized to go after those niche markets. So you're not gonna be competing against Google and Microsoft and Intuit for the most part, if you go after a really niche market. And that is a great advantage. You can make a very good business that pays you enough to live in like, you know, cross stitch or religious history, but like it's not a scalable business. Like you're never gonna build a billion dollar business that way, but like you can do very, very well for yourself as a small indie developer that way. So that's where I'd start. Start with what you know and do something other than software dev tools.

</details>

## Breaking into tech

### `06-job-boards-are-dead.mp4`

**Suggested post:** Nobody is using job websites anymore  
**Slug:** `job-boards-are-dead-networking`  
**Length:** 38.4s (18.3 MB) · **Layout:** head · **Source:** 40:38.4-40:58.1 + 41:11.3-41:29.9

Post a job now and you get thousands of AI-written applications nobody can sort through. Applying online has become a losing game, which makes who you know matter more than it ever has.

*Tags:* tech jobs, job search, networking, careers in tech, hiring

> Assembled from 2 source segments. Internal cut drops an off-hand line about scammers by nationality; the clip keeps the argument and lands on 'it is who you know'.

*Gemini review:* hook 4/5 · clarity 5/5 · captions 4/5 · framing 4/5 · edit 4/5 · audio 4/5 · publish-ready: yes

<details><summary>Transcript</summary>

nobody is using job websites anymore. So like applying online is like a losing game these days. Everybody I know who has posted a job online has gotten like thousands of applications because everybody's using AI to apply now. And so they just get overwhelmed and they don't even know what's real. So it like more than ever, it is who you know. That has always been true but it is more true now than ever. And it's not really because anybody like made the decision to do that. It's just because the internet has gotten like so flooded with all this fake stuff that like, you know we don't know what else to do.

</details>

