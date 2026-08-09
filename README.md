# 👋 Hi, I'm HoGenny

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=220&section=header&text=HoGenny%20%F0%9F%91%8B&fontSize=48&fontAlignY=35&desc=AI%20Researcher%20in%20Progress&descAlignY=60" width="100%"/>
</p>

<p align="center">
  <a href="https://github.com/HoGenny">
    <img src="https://img.shields.io/badge/GitHub-HoGenny-181717?style=flat-square&logo=github" />
  </a>
  <img src="https://img.shields.io/badge/Computer%20Engineering-Gachon%20University-2ea44f?style=flat-square" />
  <img src="https://img.shields.io/badge/AI%20Research-Computer%20Vision-58A6FF?style=flat-square" />
</p>

<p align="center">
  <b>AI Researcher in Progress · Computer Vision · Medical AI</b>
</p>

---

## 🧑‍🔬 About Me

안녕하세요, **신호진(HoGenny)**입니다.

가천대학교 컴퓨터공학과에서 공부하며
**AI 모델을 이해하고, 연구 문제를 정의하고, 실제 시스템으로 구현하는 과정**에 관심을 가지고 있습니다.

현재 **가천대학교 INES Lab AI Team**에서 학부연구생으로 활동하며
**Medical AI와 Prosthetic Vision**을 중심으로 연구하고 있습니다.

특히 제한된 시각 정보 환경에서 사용자가 **실제로 필요한 정보를 어떻게 인지할 수 있는가**에 관심이 있습니다.

> **My research question**
> *"In a limited prosthetic vision environment, what visual information should be preserved for functional perception?"*

### 🎯 Research Interests

* 🧠 Computer Vision
* 👁️ Prosthetic Vision
* 🏥 Medical AI
* 🎯 Visual Information Prioritization
* 🖼️ Image Representation & Simplification
* 🤖 Deep Learning
* 📊 Human-Centered AI

---

## 🔬 Undergraduate Researcher

### INES Lab · AI Team

**Gachon University · Undergraduate Researcher**

현재 연구의 핵심 관심사는 **제한된 시각 정보 환경에서 기능적 지각을 위해 어떤 정보를 보존해야 하는가**입니다.

기존의 단순한 객체 검출이나 이미지 압축을 넘어,

**Scene → Information Priority → Visual Simplification → Functional Perception**

의 관점에서 시각 정보를 선택적으로 표현하는 방법을 연구하고 있습니다.

### 🧠 Current Research

**Priority-Aware Multi-Layer Visual Simplification for Prosthetic Vision**

제한된 해상도와 정보량을 가진 prosthetic vision 환경에서
모든 시각 정보를 동일하게 표현하는 대신 **과제와 문맥에 따라 중요한 정보를 우선적으로 보존**하는 접근을 연구하고 있습니다.

#### Research Pipeline

```text
Input Image
     │
     ▼
Object Detection ──────┐
                       │
Depth Estimation ──────┤
                       ▼
              Information Priority
                       │
                       ▼
             Multi-Layer Representation
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          Primary   Secondary   Structural
           Object    Objects      Edges
             │         │         │
             └─────────┼─────────┘
                       ▼
             Prosthetic Vision
               Representation
                       │
                       ▼
             Functional Perception
```

### 🔍 Research Focus

* 제한된 시각 정보에서 **중요 정보의 우선순위 결정**
* Object Detection 기반 scene understanding
* Depth 정보를 활용한 spatial priority
* Primary / Secondary / Structural information의 계층적 표현
* 제한된 pixel budget에서 정보량 제어
* Human labeling 및 weak supervision
* Human–AI agreement 분석
* 행동 실험을 통한 perceptual validation
* 다양한 환경 및 해상도에서의 일반화

### 🧪 Research Tools

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,pytorch,opencv&perline=6" />
</p>

**Models & Frameworks**

* PyTorch
* YOLO / SSD
* MiDaS
* Vision Transformer
* Swin Transformer
* Diffusion Models
* Hugging Face Transformers

**Datasets & Simulation**

* COCO
* SANPO
* ProcTHOR

**Evaluation**

* Object Preservation
* Primary Visibility
* Activated Pixel Ratio
* Edge Density
* Inference Time
* Human–AI Agreement
* Behavioral Evaluation

---

## 📚 Research & Study

현재 연구를 진행하면서 단순히 모델을 사용하는 것보다
**논문의 아이디어를 이해하고 직접 구현하는 것**을 중요하게 생각하고 있습니다.

### Topics I'm Studying

```text
Deep Learning
├── CNN
├── Object Detection
├── Vision Transformer
├── Diffusion Models
└── Representation Learning

Computer Vision
├── Scene Understanding
├── Object Detection
├── Depth Estimation
├── Image Representation
└── Visual Perception

Medical AI
├── Prosthetic Vision
├── Human-Centered AI
└── Assistive Technology

Research Methodology
├── Experimental Design
├── Human Evaluation
├── Statistical Analysis
└── Reproducible Research
```

---

## 🛠️ Technical Skills

### AI / Machine Learning

<p>
  <img src="https://skillicons.dev/icons?i=python,pytorch&perline=8" />
</p>

* Python / PyTorch
* Hugging Face Transformers
* Computer Vision
* Object Detection
* Depth Estimation
* Transformer Architecture
* Diffusion Models
* Data Processing & Evaluation

### Backend / Cloud

<p>
  <img src="https://skillicons.dev/icons?i=nodejs,express,aws,mongodb,dynamodb,s3,linux&perline=8" />
</p>

* Node.js / Express
* AWS Lambda
* API Gateway
* DynamoDB
* S3
* MongoDB
* Linux

### Development Tools

<p>
  <img src="https://skillicons.dev/icons?i=git,github,docker&perline=8" />
</p>

* Git / GitHub
* Docker
* Gradio
* Jupyter
* VS Code

---

## 💻 Selected Projects

### 🧠 BERT-based Korean Question Answering

**2025.05 – 2025.06**

한국어 Machine Reading Comprehension 기반 질의응답 시스템

**Role**

* Dataset preprocessing
* Model fine-tuning
* Inference pipeline
* Web demo implementation

**Tech**
`Python` `PyTorch` `Hugging Face` `Gradio`

**Highlights**

* KLUE-MRC 기반 `kcbert-base` fine-tuning
* 긴 문서 처리를 위한 **Sliding Window** 적용
* Gradio 기반 interactive QA demo 구현

---

### 👁️ Prosthetic Vision Research

**Undergraduate Research · INES Lab**

제한된 시각 환경에서 기능적 지각을 위한
**Priority-Aware Multi-Layer Visual Simplification** 연구

**Tech**

`PyTorch` `Computer Vision` `YOLO` `SSD` `MiDaS` `COCO` `ProcTHOR` `SANPO`

**Highlights**

* Scene-level visual information prioritization
* Depth-aware information selection
* Multi-layer visual representation
* Limited pixel budget optimization
* Human labeling & agreement analysis
* Behavioral evaluation design

> **Research in progress**

---

### ☁️ AWS Serverless AI Guestbook

**2025.11**

AWS Serverless Architecture를 활용한 AI 방명록 서비스

**Role**

* Cloud architecture
* Backend development
* AI service integration

**Tech**

`AWS Lambda` `API Gateway` `DynamoDB` `S3` `Comprehend` `Node.js`

**Highlights**

* Serverless architecture 설계
* Amazon Comprehend 기반 부정 텍스트 필터링
* API → Database → AI service 전체 pipeline 구현

---

### 🌐 Polioo — Portfolio Generation Platform

**2025.04 – 2025.05**

사용자 입력을 기반으로 개인 포트폴리오 페이지를 자동 생성하는 플랫폼

**Role**

* Backend development
* Template engine

**Tech**

`Node.js` `Express` `MongoDB` `AWS S3`

**Highlights**

* 사용자 입력 기반 정적 HTML 자동 생성
* S3 Static Hosting을 활용한 배포
* Backend → Storage → Deployment workflow 구현

---

## 🏆 Achievements

### 제6회 대한민국 신직업·미래직업 아이디어 공모전

**2025.08**

**건물 에너지 효율화 컨설턴트**

ZEB 의무화 정책 및 시장 분석을 기반으로
기후위기 대응을 위한 융합형 미래 직업을 제안했습니다.

---

## 📖 What I'm Working On

```text
NOW
 │
 ├─ 🔬 Prosthetic Vision Research
 │
 ├─ 🧠 Computer Vision & Deep Learning
 │
 ├─ 📄 Reading & Reproducing Research Papers
 │
 ├─ 🧪 Designing Human-centered Experiments
 │
 └─ 🎓 Preparing for Graduate Research
```

### Current Goal

> **From implementing models to conducting research.**

단순히 최신 AI 모델을 사용하는 개발자가 아니라,

**문제를 정의하고 → 가설을 세우고 → 모델을 설계하고 → 실험하고 → 결과를 검증하는**

연구자로 성장하는 것을 목표로 하고 있습니다.

---

## 📫 Contact

<p align="center">
  <a href="mailto:tyui3024@icloud.com">
    <img src="https://img.shields.io/badge/Email-tyui3024%40icloud.com-31363F?style=for-the-badge&logo=icloud&logoColor=white" />
  </a>
  <a href="https://github.com/HoGenny">
    <img src="https://img.shields.io/badge/GitHub-HoGenny-181717?style=for-the-badge&logo=github&logoColor=white" />
  </a>
</p>

---

<p align="center">
  <i>Research · Build · Validate · Iterate</i>
</p>
