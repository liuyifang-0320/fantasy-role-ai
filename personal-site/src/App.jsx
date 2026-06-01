import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  Bot,
  BrainCircuit,
  BriefcaseBusiness,
  Code2,
  Cpu,
  Database,
  ExternalLink,
  Github,
  GraduationCap,
  Layers,
  MapPin,
  Rocket,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";

const projects = [
  {
    title: "JARVIS Plan｜个人操作系统助理",
    type: "AI Agent / Python / 本地记忆",
    desc: "围绕“自然语言任务执行”设计的个人助理原型，把复杂指令拆成文件读取、待办生成、总结沉淀和日历输出等可执行动作。",
    highlights: ["任务拆解", "memory_store", "Markdown 总结", ".ics 日历"],
    icon: Bot,
  },
  {
    title: "幻梦数字人｜剧本杀角色 AI 系统",
    type: "UniApp / Vue 3 / FastAPI / SQLAlchemy",
    desc: "面向剧本杀与恋陪数字人的小程序和后端工程骨架，已跑通资料解析、角色候选、关系网络、知识检索、聊天、长期记忆和自动化验收主链路。",
    highlights: ["资料解析", "角色生成", "长期记忆", "Q 版桌宠"],
    icon: Sparkles,
    link: "https://github.com/liuyifang-0320/fantasy-role-ai",
  },
  {
    title: "AI 水质预警模型",
    type: "Machine Learning / Random Forest / Data Analysis",
    desc: "基于真实水质数据完成异常预警模型，从数据清洗、特征处理、模型训练到指标评估和中文可视化报告形成完整闭环。",
    highlights: ["Precision", "Recall", "F1", "PR-AUC"],
    icon: Activity,
  },
  {
    title: "AI Note｜手写问答笔记",
    type: "Frontend / OCR / LLM API",
    desc: "探索 AI 学习工具的人机交互原型，包含手写画布、框选识别、OCR、后端问答和手写风格答案绘制。",
    highlights: ["Canvas", "OCR", "AI 问答", "手写输出"],
    icon: Code2,
  },
];

const skillGroups = [
  {
    icon: Code2,
    title: "开发基础",
    items: ["Python", "JavaScript", "HTML / CSS", "FastAPI", "Vue / React"],
  },
  {
    icon: BrainCircuit,
    title: "AI 方向",
    items: ["机器学习", "Prompt Engineering", "RAG", "AI Agent", "数据分析"],
  },
  {
    icon: Database,
    title: "工程能力",
    items: ["SQLite", "文件解析", "项目文档", "需求拆解", "MVP 验收"],
  },
];

const operatingSystem = [
  {
    icon: Workflow,
    title: "把想法拆成流程",
    body: "先明确用户场景、输入输出和验收标准，再把模糊需求压成能开发的模块。",
  },
  {
    icon: Cpu,
    title: "用 AI 做真实产品",
    body: "关注模型能力，也关注工程边界、fallback、数据结构和可复盘的执行链路。",
  },
  {
    icon: ShieldCheck,
    title: "交付可验证结果",
    body: "为核心功能补自动化检查，让项目不只停留在 demo，而是能继续迭代。",
  },
];

const stats = [
  ["4+", "项目作品"],
  ["AI", "主攻方向"],
  ["MVP", "执行方法"],
  ["上海", "目标城市"],
];

const fadeUp = {
  hidden: { opacity: 0, y: 22 },
  visible: { opacity: 1, y: 0 },
};

function NeuralCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const pointer = { x: -1000, y: -1000 };
    let width = 0;
    let height = 0;
    let points = [];
    let frame = 0;

    const makePoints = () => {
      const count = Math.max(48, Math.min(96, Math.floor((width * height) / 19000)));
      points = Array.from({ length: count }, (_, index) => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.28,
        vy: (Math.random() - 0.5) * 0.28,
        r: index % 9 === 0 ? 2.4 : 1.35,
      }));
    };

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      width = canvas.offsetWidth;
      height = canvas.offsetHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      makePoints();
    };

    const movePointer = (event) => {
      const rect = canvas.getBoundingClientRect();
      pointer.x = event.clientX - rect.left;
      pointer.y = event.clientY - rect.top;
    };

    const leavePointer = () => {
      pointer.x = -1000;
      pointer.y = -1000;
    };

    const draw = () => {
      frame = requestAnimationFrame(draw);
      ctx.clearRect(0, 0, width, height);

      ctx.fillStyle = "#050505";
      ctx.fillRect(0, 0, width, height);

      ctx.strokeStyle = "rgba(255, 255, 255, 0.035)";
      ctx.lineWidth = 1;
      for (let x = 0; x < width; x += 72) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += 72) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      points.forEach((point) => {
        point.x += point.vx;
        point.y += point.vy;
        if (point.x < 0 || point.x > width) point.vx *= -1;
        if (point.y < 0 || point.y > height) point.vy *= -1;

        const dx = point.x - pointer.x;
        const dy = point.y - pointer.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 132) {
          point.x += dx * 0.004;
          point.y += dy * 0.004;
        }
      });

      for (let i = 0; i < points.length; i += 1) {
        for (let j = i + 1; j < points.length; j += 1) {
          const a = points[i];
          const b = points[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 138) {
            const alpha = (1 - dist / 138) * 0.16;
            ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      points.forEach((point, index) => {
        const pulse = 0.82 + Math.sin(Date.now() / 900 + index) * 0.12;
        ctx.fillStyle = index % 7 === 0 ? "rgba(255, 255, 255, 0.82)" : "rgba(210, 210, 205, 0.54)";
        ctx.beginPath();
        ctx.arc(point.x, point.y, point.r * pulse, 0, Math.PI * 2);
        ctx.fill();
      });
    };

    resize();
    draw();
    window.addEventListener("resize", resize);
    canvas.addEventListener("pointermove", movePointer);
    canvas.addEventListener("pointerleave", leavePointer);

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("pointermove", movePointer);
      canvas.removeEventListener("pointerleave", leavePointer);
    };
  }, []);

  return <canvas className="neural-canvas" ref={canvasRef} aria-hidden="true" />;
}

function App() {
  return (
    <div className="site-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="回到首页">
          <span className="brand-mark">LYF</span>
          <span>
            <strong>刘易枋</strong>
            <small>AI Builder Portfolio</small>
          </span>
        </a>
        <nav className="nav-links" aria-label="主导航">
          <a href="#projects">项目</a>
          <a href="#skills">能力</a>
          <a href="#system">方法</a>
          <a href="#contact">联系</a>
        </nav>
        <a className="icon-action" href="https://github.com/liuyifang-0320" target="_blank" rel="noreferrer" aria-label="打开 GitHub">
          <Github size={20} />
        </a>
      </header>

      <main id="top">
        <section className="hero">
          <NeuralCanvas />
          <div className="hero-overlay" />
          <div className="hero-inner">
            <motion.div className="hero-copy" initial="hidden" animate="visible" variants={fadeUp} transition={{ duration: 0.65 }}>
              <span className="status-pill">
                <Rocket size={16} />
                正在寻找 AI / 后端 / 数据方向实习机会
              </span>
              <h1>
                刘易枋
                <span>AI 产品建造者</span>
              </h1>
              <p>
                人工智能专业本科在读，关注 AI Agent、机器学习、数据分析与产品原型开发。相比只停在概念，我更喜欢把需求拆清楚、做出 MVP、跑通流程，再整理成可展示、可复盘、可继续迭代的作品。
              </p>
              <div className="hero-actions">
                <a className="primary-action" href="#projects">
                  看项目
                  <ArrowRight size={18} />
                </a>
                <a className="secondary-action" href="https://github.com/liuyifang-0320/fantasy-role-ai" target="_blank" rel="noreferrer">
                  GitHub 仓库
                  <ExternalLink size={17} />
                </a>
              </div>
            </motion.div>

            <motion.aside className="signal-panel" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.75, delay: 0.16 }}>
              <div className="panel-header">
                <span />
                <span />
                <span />
                <strong>candidate.profile</strong>
              </div>
              <div className="profile-line">
                <GraduationCap size={18} />
                上海立达学院 · 人工智能专业
              </div>
              <div className="profile-line">
                <BriefcaseBusiness size={18} />
                目标岗位：AI / 后端 / 数据开发实习
              </div>
              <div className="profile-line">
                <MapPin size={18} />
                期望城市：上海
              </div>
              <div className="metric-grid">
                {stats.map(([value, label]) => (
                  <div className="metric" key={label}>
                    <strong>{value}</strong>
                    <span>{label}</span>
                  </div>
                ))}
              </div>
            </motion.aside>
          </div>
        </section>

        <section className="section intro-section">
          <motion.div className="section-heading" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.25 }} variants={fadeUp} transition={{ duration: 0.55 }}>
            <span>About</span>
            <h2>我正在建立自己的 AI 工程能力栈。</h2>
          </motion.div>
          <motion.p className="wide-text" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.25 }} variants={fadeUp} transition={{ duration: 0.55, delay: 0.08 }}>
            我目前系统补齐编程、机器学习、前端和工程化能力。我的优势不是只会写概念，而是愿意把一个想法拆成需求、流程、原型和验收标准，再持续迭代成能展示的作品。当前重点方向是 AI Agent、个人助理系统、剧本角色数字人、数据分析与机器学习应用。
          </motion.p>
        </section>

        <section className="section" id="projects">
          <div className="section-row">
            <div className="section-heading">
              <span>Projects</span>
              <h2>代表项目</h2>
            </div>
            <p>
              这些项目覆盖 AI 应用、数据建模、产品拆解和工程实现，展示从想法到交付的完整成长轨迹。
            </p>
          </div>
          <div className="project-grid">
            {projects.map((project, index) => {
              const Icon = project.icon;
              return (
                <motion.article
                  className="project-card"
                  key={project.title}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, amount: 0.2 }}
                  variants={fadeUp}
                  transition={{ duration: 0.48, delay: index * 0.07 }}
                >
                  <div className="project-topline">
                    <span className="project-icon">
                      <Icon size={21} />
                    </span>
                    <span>{project.type}</span>
                  </div>
                  <h3>{project.title}</h3>
                  <p>{project.desc}</p>
                  <div className="tag-row">
                    {project.highlights.map((item) => (
                      <span key={item}>{item}</span>
                    ))}
                  </div>
                  {project.link && (
                    <a className="text-link" href={project.link} target="_blank" rel="noreferrer">
                      查看项目仓库
                      <ExternalLink size={16} />
                    </a>
                  )}
                </motion.article>
              );
            })}
          </div>
        </section>

        <section className="section" id="skills">
          <div className="section-heading">
            <span>Skills</span>
            <h2>能力结构</h2>
          </div>
          <div className="skills-grid">
            {skillGroups.map((group, index) => {
              const Icon = group.icon;
              return (
                <motion.article
                  className="skill-card"
                  key={group.title}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, amount: 0.25 }}
                  variants={fadeUp}
                  transition={{ duration: 0.48, delay: index * 0.08 }}
                >
                  <Icon size={24} />
                  <h3>{group.title}</h3>
                  <ul>
                    {group.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </motion.article>
              );
            })}
          </div>
        </section>

        <section className="section system-section" id="system">
          <div className="section-heading">
            <span>Operating System</span>
            <h2>我的做项目方式</h2>
          </div>
          <div className="system-grid">
            {operatingSystem.map((item, index) => {
              const Icon = item.icon;
              return (
                <motion.article
                  className="system-item"
                  key={item.title}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, amount: 0.25 }}
                  variants={fadeUp}
                  transition={{ duration: 0.48, delay: index * 0.08 }}
                >
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <Icon size={22} />
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </motion.article>
              );
            })}
          </div>
        </section>

        <section className="contact-section" id="contact">
          <div>
            <span>Contact</span>
            <h2>欢迎交流实习、项目合作与 AI 产品想法。</h2>
            <p>
              我正在寻找能真实参与项目、积累工程经验和 AI 应用经验的机会。如果你对我的项目或能力感兴趣，可以通过 GitHub 联系我。
            </p>
          </div>
          <div className="contact-actions">
            <a className="primary-action" href="https://github.com/liuyifang-0320" target="_blank" rel="noreferrer">
              打开 GitHub
              <Github size={18} />
            </a>
            <a className="secondary-action" href="https://github.com/liuyifang-0320/fantasy-role-ai" target="_blank" rel="noreferrer">
              查看幻梦数字人
              <Layers size={18} />
            </a>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
