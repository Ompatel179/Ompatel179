<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-dark.svg">
  <img src="assets/header-light.svg" alt="Om Patel: ML engineer / backend / full stack. Rutgers University, New Brunswick, NJ, MS CS graduating May 2027. Illustration of a desk with a laptop sharpening a pixelated image, with a satellite orbiting above." width="100%">
</picture>

## Hey, I'm Om.

I'm a computer science master's student at Rutgers University–New Brunswick, graduating in May 2027. I work mostly on machine learning, plus the backend and frontend that put a model in front of real people.

I learn by building something and then measuring it. I load-test my own APIs until something breaks, benchmark my models against the baselines, and treat the numbers as the to-do list. That's how EventPass went from freezing at 13 requests a second to serving about 950.

Before grad school I did research on deep learning for satellite imagery, which led to an IEEE paper. Before that, I wrote firmware that read cryogenic liquid levels from noisy sensors. I like problems where software meets the messy real world.

**Open to roles starting May 2027:** full-time, part-time or internship, in ML, backend or full stack.

[Selected work](#selected-work) · [Tech stack](#tech-stack) · [Recent activity](#recent-activity) · [Get in touch](#get-in-touch)

### Now building

- **A RAG project:** LLM answers grounded in real documents, with retrieval quality I can actually measure.
- **My portfolio site**, coming right after this page.

## Selected work

<!-- PROJECTS:START -->
<table>
<tr>
<td width="50%" valign="top">
<a href="https://github.com/Ompatel179/Eventpass"><b>EventPass ↗</b></a> &nbsp;<picture><source media="(prefers-color-scheme: dark)" srcset="assets/status-shipped-dark.svg"><img src="assets/status-shipped-light.svg" alt="shipped" height="20"></picture>
<p>QR-code check-in for student clubs. Students get a ticket, organizers scan it at the door from a phone, and every ticket checks in exactly once, even when several organizers scan at the same moment.</p>
<p><b>0 duplicates</b> · 2,862 concurrent scans, ~950 req/s on one worker after I found and fixed a deadlock, 97% test coverage</p>
<p><code>FastAPI</code> <code>PostgreSQL</code> <code>Redis</code> <code>Docker</code> <code>Locust</code></p>
</td>
<td width="50%" valign="top">
<a href="https://github.com/Ompatel179/Harnessing_Generative_Adversarial_Models_to_Enhance_Satellite_Imagery_Quality"><b>Satellite SRGAN ↗</b></a> &nbsp;<picture><source media="(prefers-color-scheme: dark)" srcset="assets/status-published-dark.svg"><img src="assets/status-published-light.svg" alt="published" height="20"></picture>
<p>A super-resolution GAN that sharpens satellite images 4×, trained in two stages: MSE pre-training, then adversarial fine-tuning with a VGG19 perceptual loss.</p>
<p><b>Published at IEEE ICETA 2025</b> · 34.55 dB PSNR and 0.08 LPIPS in the paper</p>
<p><code>PyTorch</code> <code>GANs</code> <code>VGG19</code> <code>OpenCV</code></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<a href="https://composur.tech"><b>Composur ↗</b></a> &nbsp;<picture><source media="(prefers-color-scheme: dark)" srcset="assets/status-live-dark.svg"><img src="assets/status-live-light.svg" alt="live" height="20"></picture><br><sub>built with <a href="https://github.com/RishiiShah">@RishiiShah</a></sub>
<p>Practice technical interviews out loud. An LLM interviewer listens, asks adaptive follow-ups and scores the answers you actually gave.</p>
<p><b>28 interview domains</b> · speech recognition → streaming LLM → text-to-speech</p>
<p><code>Next.js</code> <code>TypeScript</code> <code>PostgreSQL</code> <code>Groq</code> <code>AWS S3</code></p>
</td>
<td width="50%" valign="top">
<b>RAG project</b> &nbsp;<picture><source media="(prefers-color-scheme: dark)" srcset="assets/status-in-progress-dark.svg"><img src="assets/status-in-progress-light.svg" alt="in progress" height="20"></picture>
<p>A retrieval-augmented generation system: LLM answers grounded in real documents, with retrieval quality I can measure instead of guess.</p>
<p><b>Building now</b> · this cell turns into a real link when the repo goes public</p>
<p><code>Python</code> <code>LLMs</code> <code>Embeddings</code> <code>Vector search</code></p>
</td>
</tr>
</table>
<!-- PROJECTS:END -->

<details>
<summary><b>More projects</b></summary>
<br>

<!-- MORE:START -->
- **[Jobnova agents](https://github.com/Ompatel179/Jobnova)**: Take-home for an AI engineer role: a Playwright agent that finds companies' career pages and open roles, plus a Chrome extension that fills Lever applications from a profile.  
  <sub>Python · Flask · Playwright · Chrome extension (MV3)</sub>
- **[Plant disease prediction](https://github.com/Ompatel179/Plant_disease_prediction)**: CNN that identifies plant diseases from leaf photos, with a Streamlit app for predictions.  
  <sub>TensorFlow · Keras · OpenCV · Streamlit</sub>
<!-- MORE:END -->

</details>

## Tech stack

<p align="center">
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/panel-ml-ai-dark.svg"><img src="assets/panel-ml-ai-light.svg" alt="ML and AI: PyTorch, TensorFlow, Keras, OpenCV, LLM APIs."></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/panel-backend-data-dark.svg"><img src="assets/panel-backend-data-light.svg" alt="Backend and data: Python, FastAPI, Flask, PostgreSQL, Redis, SQLAlchemy."></picture>
</p>
<p align="center">
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/panel-full-stack-dark.svg"><img src="assets/panel-full-stack-light.svg" alt="Full stack: TypeScript, Next.js, Prisma, JavaScript, HTML and CSS."></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/panel-ship-test-dark.svg"><img src="assets/panel-ship-test-light.svg" alt="Ship and test: Docker, GitHub Actions, Vercel, AWS S3, Locust."></picture>
</p>
<p align="center">
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/panel-learning-dark.svg"><img src="assets/panel-learning-light.svg" alt="Learning right now: Kubernetes, RAG and vector search, React in more depth, AWS beyond S3."></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/panel-languages-dark.svg"><img src="assets/panel-languages-light.svg" alt="Language mix across my public repositories, by bytes of code, notebooks excluded."></picture>
</p>

<details>
<summary><b>How I'm learning the in-progress ones</b></summary>
<br>

I build something small with each one, so it ends up in a repo and not just in my notes.

- **RAG and vector search:** chunking, embeddings and retrieval evaluation, all going into the RAG project above.
- **Kubernetes:** taking EventPass from Docker Compose to a small cluster deployment.
- **React, deeper:** state, data fetching and component design beyond what Next.js gave me in Composur.
- **AWS beyond S3:** compute and deployment services, so I can host my own projects end to end.

</details>

<details>
<summary><b>More about me</b></summary>
<br>

- MS in Computer Science at **Rutgers University–New Brunswick** (graduating May 2027). B.Tech in ICT from PDEU, India.
- Published **"Harnessing Generative Adversarial Models to Enhance Satellite Imagery Quality"** at IEEE ICETA 2025.
- Research intern in deep learning: U-Nets for change detection on satellite imagery (89% IoU).
- Part-time at Rutgers Career Exploration and Success: I build an internal web dashboard for employers and wrote the mentor–mentee matching algorithm. That code isn't public, which is why this page shows only personal projects.

</details>

## Recent activity

<!-- ACTIVITY:START -->
- Merged PR [#16](https://github.com/Ompatel179/Eventpass/pull/16) *Enforce event capacity with a row lock, fix ticket card bug, update README with screenshots* in [Eventpass](https://github.com/Ompatel179/Eventpass) <sub>·&nbsp;Nov&nbsp;12</sub>
- Merged PR [#15](https://github.com/Ompatel179/Eventpass/pull/15) *Add full website: public events, sign-up, tickets, organizer dashboard, shared scanner login* in [Eventpass](https://github.com/Ompatel179/Eventpass) <sub>·&nbsp;Nov&nbsp;12</sub>
- Merged PR [#14](https://github.com/Ompatel179/Eventpass/pull/14) *Store all times as timestamptz and require time zones in the API* in [Eventpass](https://github.com/Ompatel179/Eventpass) <sub>·&nbsp;Nov&nbsp;12</sub>
- Merged PR [#13](https://github.com/Ompatel179/Eventpass/pull/13) *Add README with architecture, design decisions and load-test results* in [Eventpass](https://github.com/Ompatel179/Eventpass) <sub>·&nbsp;Nov&nbsp;09</sub>
- Merged PR [#12](https://github.com/Ompatel179/Eventpass/pull/12) *Index registrations by user* in [Eventpass](https://github.com/Ompatel179/Eventpass) <sub>·&nbsp;Nov&nbsp;09</sub>
<!-- ACTIVITY:END -->

## Get in touch

I'm happy to talk about ML systems, backend performance, or a role you think I'd fit.

- LinkedIn: [linkedin.com/in/op179](https://www.linkedin.com/in/op179/)
- Email: [omnpatel179@gmail.com](mailto:omnpatel179@gmail.com)
- Resumes: [ML / AI](resume/Om_Patel_Resume_ML_AI.pdf) · [Software engineering](resume/Om_Patel_Resume_SWE.pdf) · [Forward-deployed engineering](resume/Om_Patel_Resume_FDE.pdf)
<!-- PORTFOLIO: replace the line below with "- Portfolio: [your-site](https://your-site)" once it's live -->
- Portfolio: coming soon

<sub>Refreshed daily by a GitHub Action. Icons from [Simple Icons](https://simpleicons.org) (CC0).</sub>
