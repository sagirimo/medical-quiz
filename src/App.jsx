import React, { useState, useEffect, useRef } from 'react';
import { CheckCircle2, XCircle, Flame, Trophy, BookOpen, ArrowRight, RotateCcw, AlertCircle, Layers, ChevronRight, FileText, Stethoscope } from 'lucide-react';

// 从public目录加载题库数据
const loadQuizData = async () => {
  const subjects = ['儿科学', '内科学', '外科学', '妇产科学'];
  const data = {};

  for (const subject of subjects) {
    try {
      const res = await fetch(`./${subject}.json`);
      if (res.ok) {
        data[subject] = await res.json();
      }
    } catch (e) {
      console.error(`加载${subject}失败:`, e);
    }
  }
  return data;
};

// 转换章节格式数据为套卷格式
const convertToExamSets = (rawData) => {
  const examSets = [];
  const gradients = [
    'from-pink-500 to-rose-600',
    'from-blue-500 to-indigo-600',
    'from-emerald-500 to-teal-600',
    'from-purple-500 to-violet-600'
  ];
  const badges = ['儿科精选', '内科精要', '外科专练', '妇产通关'];

  Object.entries(rawData).forEach(([subject, chapters], idx) => {
    const questions = [];
    Object.entries(chapters).forEach(([chapter, qs]) => {
      qs.forEach(q => {
        questions.push({
          id: q.id,
          chapter: chapter,
          type: 'mcq',
          question: q.question,
          options: q.options,
          correctAnswer: q.correctAnswer,
          explanation: q.explanation || ''
        });
      });
    });

    examSets.push({
      id: `exam_${subject}`,
      title: `北医${subject}题库`,
      badge: badges[idx] || '真题精选',
      description: `收录${subject}${questions.length}道真题，覆盖${Object.keys(chapters).length}个核心章节。智能刷题，考前必备。`,
      questions: questions,
      gradient: gradients[idx] || 'from-slate-500 to-gray-600'
    });
  });

  return examSets;
};

// 撒花组件
const Confetti = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    const colors = ['#f43f5e', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];

    for (let i = 0; i < 200; i++) {
      particles.push({
        x: canvas.width / 2,
        y: canvas.height + 10,
        r: Math.random() * 6 + 4,
        dx: Math.random() * 12 - 6,
        dy: Math.random() * -18 - 10,
        color: colors[Math.floor(Math.random() * colors.length)],
        tilt: Math.floor(Math.random() * 10) - 10,
        tiltAngleInc: (Math.random() * 0.07) + 0.05,
        tiltAngle: 0
      });
    }

    let animationFrame;
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach((p) => {
        p.tiltAngle += p.tiltAngleInc;
        p.y += p.dy;
        p.x += Math.sin(p.tiltAngle) * 2 + p.dx;
        p.dy += 0.2;
        ctx.beginPath();
        ctx.lineWidth = p.r;
        ctx.strokeStyle = p.color;
        ctx.moveTo(p.x + p.tilt + p.r, p.y);
        ctx.lineTo(p.x + p.tilt, p.y + p.tilt + p.r);
        ctx.stroke();
      });
      animationFrame = requestAnimationFrame(render);
    };
    render();

    return () => cancelAnimationFrame(animationFrame);
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-50" />;
};

// 主应用组件
export default function MedicalQuiz() {
  const [examSets, setExamSets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [gameState, setGameState] = useState('home');
  const [activeExamData, setActiveExamData] = useState(null);

  const [selectedChapter, setSelectedChapter] = useState('全部题目');
  const [filteredData, setFilteredData] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const [selectedOption, setSelectedOption] = useState(null);
  const [isAnswered, setIsAnswered] = useState(false);

  const [score, setScore] = useState(0);
  const [streak, setStreak] = useState(0);
  const [maxStreak, setMaxStreak] = useState(0);
  const [wrongAnswers, setWrongAnswers] = useState([]);
  const [shake, setShake] = useState(false);

  // 加载数据
  useEffect(() => {
    loadQuizData().then(data => {
      const exams = convertToExamSets(data);
      setExamSets(exams);
      setLoading(false);
    });
  }, []);

  const handleSelectExam = (exam) => {
    setActiveExamData(exam);
    setGameState('examDetail');
  };

  const handleStartChapter = (chapter) => {
    const list = chapter === '全部题目'
      ? activeExamData.questions
      : activeExamData.questions.filter(q => q.chapter === chapter);

    setFilteredData(list);
    setSelectedChapter(chapter);
    setGameState('playing');
    setCurrentQuestionIndex(0);
    setScore(0);
    setStreak(0);
    setMaxStreak(0);
    setWrongAnswers([]);
    setSelectedOption(null);
    setIsAnswered(false);
  };

  const currentQuestion = filteredData[currentQuestionIndex];
  const progress = filteredData.length > 0 ? ((currentQuestionIndex) / filteredData.length) * 100 : 0;

  const handleOptionClick = (index) => {
    if (isAnswered) return;
    setSelectedOption(index);
    setIsAnswered(true);

    if (index === currentQuestion.correctAnswer) {
      setScore(score + 1);
      const newStreak = streak + 1;
      setStreak(newStreak);
      if (newStreak > maxStreak) setMaxStreak(newStreak);
    } else {
      setStreak(0);
      triggerShake();
      setWrongAnswers(prev => [...prev, { question: currentQuestion, userAnswer: index }]);
    }
  };

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 500);
  };

  const handleNext = () => {
    if (currentQuestionIndex < filteredData.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setSelectedOption(null);
      setIsAnswered(false);
    } else {
      setGameState('result');
    }
  };

  const getStreakMessage = () => {
    if (streak >= 15) return "🏆 独孤求败！";
    if (streak >= 10) return "🔥 神乎其技！";
    if (streak >= 5) return "🔥 势如破竹！";
    if (streak >= 3) return "🔥 渐入佳境！";
    return null;
  };

  const customStyles = `
    @keyframes shake { 0%, 100% { transform: translateX(0); } 10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); } 20%, 40%, 60%, 80% { transform: translateX(5px); } }
    .animate-shake { animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; }
    .glass-panel { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
  `;

  // 加载中
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 font-bold text-lg">正在加载题库...</p>
        </div>
      </div>
    );
  }

  // 主页
  if (gameState === 'home') {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center py-12 px-4 sm:px-6">
        <style>{customStyles}</style>
        <div className="w-full max-w-5xl">
          <div className="text-center mb-12">
            <div className="w-24 h-24 bg-gradient-to-br from-pink-500 to-rose-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-rose-500/30 transform hover:rotate-6 transition-all duration-300">
              <Stethoscope className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-4xl sm:text-5xl font-black text-slate-800 tracking-tight">北医题库刷题系统</h1>
            <p className="text-slate-500 mt-4 text-lg font-medium">四大科目 · 智能刷题 · 错题收录 · 考前必备</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {examSets.map((exam, idx) => {
              const lightBgs = [
                'bg-pink-50 border-pink-100 hover:border-pink-400',
                'bg-blue-50 border-blue-100 hover:border-blue-400',
                'bg-emerald-50 border-emerald-100 hover:border-emerald-400',
                'bg-purple-50 border-purple-100 hover:border-purple-400'
              ];
              const textColors = ['text-pink-700', 'text-blue-700', 'text-emerald-700', 'text-purple-700'];

              return (
                <div
                  key={exam.id}
                  onClick={() => handleSelectExam(exam)}
                  className={`rounded-3xl p-8 border-2 hover:shadow-2xl transition-all duration-300 cursor-pointer group flex flex-col relative overflow-hidden ${lightBgs[idx % 4]}`}
                >
                  <div className={`absolute -right-12 -top-12 w-40 h-40 rounded-full opacity-10 bg-gradient-to-br ${exam.gradient}`}></div>
                  <div className="flex justify-between items-start mb-6 relative z-10">
                    <span className={`text-xs font-black px-4 py-1.5 rounded-full uppercase tracking-widest bg-white shadow-sm ${textColors[idx % 4]}`}>
                      {exam.badge}
                    </span>
                  </div>
                  <h2 className="text-2xl font-black text-slate-800 mb-3 relative z-10 leading-tight">{exam.title}</h2>
                  <p className="text-slate-600 mb-8 flex-1 text-sm leading-relaxed relative z-10 font-medium">{exam.description}</p>
                  <div className={`flex items-center gap-2 text-sm font-bold border-t border-black/5 pt-5 mt-auto relative z-10 ${textColors[idx % 4]}`}>
                    <FileText className="w-5 h-5" />
                    <span>共 {exam.questions.length} 题</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // 章节选择
  if (gameState === 'examDetail') {
    const chapters = ["全部题目", ...new Set(activeExamData.questions.map(q => q.chapter))];

    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6">
        <style>{customStyles}</style>
        <div className="glass-panel max-w-3xl w-full p-10 sm:p-12 rounded-3xl text-center relative shadow-xl">
          <button
            onClick={() => setGameState('home')}
            className="absolute top-6 left-6 text-slate-400 hover:text-slate-800 flex items-center gap-1 font-bold transition-colors bg-white px-4 py-2 rounded-xl shadow-sm border border-slate-100"
          >
            <RotateCcw className="w-5 h-5" /> 返回大厅
          </button>

          <div className="w-24 h-24 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-6 mt-8 border-4 border-white shadow-md">
            <BookOpen className="w-12 h-12 text-blue-600" />
          </div>

          <h1 className="text-4xl font-extrabold text-slate-800 mb-4">{activeExamData.title}</h1>
          <p className="text-slate-500 mb-10 font-medium text-lg">选择章节开始练习：</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left max-h-96 overflow-y-auto">
            {chapters.map((chapter, idx) => (
              <button
                key={idx}
                onClick={() => handleStartChapter(chapter)}
                className={`p-5 rounded-2xl flex items-center justify-between transition-all duration-300 hover:-translate-y-1 ${
                  chapter === '全部题目'
                    ? 'col-span-1 sm:col-span-2 bg-slate-800 text-white shadow-xl hover:bg-black'
                    : 'bg-white border-2 border-slate-100 hover:border-blue-400 text-slate-700 hover:bg-blue-50 hover:shadow-md'
                }`}
              >
                <div className="flex items-center gap-4">
                  {chapter === '全部题目' ? <Layers className="w-7 h-7" /> : <BookOpen className="w-6 h-6 text-blue-500" />}
                  <span className="font-bold text-lg">{chapter}</span>
                </div>
                <div className="text-sm font-bold opacity-90 bg-black/10 px-4 py-1.5 rounded-full">
                  {chapter === '全部题目' ? activeExamData.questions.length : activeExamData.questions.filter(q => q.chapter === chapter).length} 题
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // 结果页
  if (gameState === 'result') {
    const accuracy = Math.round((score / filteredData.length) * 100) || 0;
    const isExcellent = accuracy >= 80;

    return (
      <div className="min-h-screen bg-slate-50 py-10 px-4 flex items-center justify-center">
        {isExcellent && <Confetti />}
        <div className="max-w-3xl w-full glass-panel rounded-3xl p-10 text-center relative z-10 shadow-2xl">
          <Trophy className={`w-28 h-28 mx-auto mb-6 ${isExcellent ? 'text-yellow-400 drop-shadow-lg' : 'text-slate-300'}`} />
          <h2 className="text-5xl font-black text-slate-800 mb-4 tracking-tight">本卷刷题完成！</h2>
          <div className="bg-slate-100 inline-block px-6 py-2 rounded-full mb-10">
            <span className="text-slate-600 font-bold">{activeExamData.title}</span>
            <span className="mx-2 text-slate-300">|</span>
            <span className="text-blue-600 font-bold">{selectedChapter}</span>
          </div>

          <div className="grid grid-cols-3 gap-6 mb-12">
            <div className="bg-white p-6 rounded-3xl border-2 border-slate-100 shadow-sm">
              <div className="text-sm text-slate-500 font-bold mb-2 uppercase tracking-widest">得分</div>
              <div className="text-5xl font-black text-rose-500">{score}<span className="text-2xl text-slate-300">/{filteredData.length}</span></div>
            </div>
            <div className="bg-white p-6 rounded-3xl border-2 border-slate-100 shadow-sm">
              <div className="text-sm text-slate-500 font-bold mb-2 uppercase tracking-widest">正确率</div>
              <div className="text-5xl font-black text-emerald-500">{accuracy}%</div>
            </div>
            <div className="bg-white p-6 rounded-3xl border-2 border-slate-100 shadow-sm">
              <div className="text-sm text-slate-500 font-bold mb-2 uppercase tracking-widest">最高连击</div>
              <div className="text-5xl font-black text-amber-500">{maxStreak}</div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {wrongAnswers.length > 0 && (
              <button
                onClick={() => setGameState('review')}
                className="flex-1 bg-rose-50 hover:bg-rose-100 text-rose-600 font-black py-5 px-6 rounded-2xl transition-all flex items-center justify-center gap-3 border-2 border-rose-200 hover:shadow-lg text-lg"
              >
                <BookOpen className="w-6 h-6" />
                复习错题 ({wrongAnswers.length})
              </button>
            )}
            <button
              onClick={() => setGameState('examDetail')}
              className="flex-1 bg-slate-800 hover:bg-black text-white font-black py-5 px-6 rounded-2xl shadow-xl hover:shadow-2xl transition-all flex items-center justify-center gap-3 transform hover:-translate-y-1 text-lg"
            >
              <RotateCcw className="w-6 h-6" />
              重新挑战
            </button>
            <button
              onClick={() => setGameState('home')}
              className="flex-none bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold py-5 px-8 rounded-2xl transition-all flex items-center justify-center text-lg"
            >
              返回大厅
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 错题本
  if (gameState === 'review') {
    return (
      <div className="min-h-screen bg-slate-50 py-10 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <div>
              <h2 className="text-3xl font-extrabold text-slate-800 flex items-center gap-3 mb-2">
                <BookOpen className="text-rose-500 w-8 h-8" />
                专属错题本
              </h2>
              <p className="text-slate-500 font-bold bg-slate-100 inline-block px-3 py-1 rounded-lg text-sm">{activeExamData.title} - {selectedChapter}</p>
            </div>
            <button
              onClick={() => setGameState('result')}
              className="text-slate-500 hover:text-slate-800 flex items-center gap-2 font-black bg-slate-100 hover:bg-slate-200 px-6 py-4 rounded-xl shadow-sm transition-colors"
            >
              返回成绩单
            </button>
          </div>

          <div className="space-y-8">
            {wrongAnswers.map((wrong, idx) => (
              <div key={idx} className="bg-white p-8 rounded-3xl border-t-8 border-t-rose-400 shadow-lg relative overflow-hidden">
                <div className="flex flex-col sm:flex-row gap-4 mb-6">
                  <span className="bg-rose-100 text-rose-600 font-black px-4 py-1.5 rounded-lg text-sm h-fit whitespace-nowrap">错题 {idx + 1}</span>
                  <span className="bg-slate-100 text-slate-500 font-bold px-3 py-1.5 rounded-lg text-sm h-fit">{wrong.question.chapter}</span>
                  <h3 className="text-xl font-bold text-slate-800 leading-relaxed">{wrong.question.question}</h3>
                </div>

                <div className="space-y-3 mb-8 pl-4 border-l-4 border-slate-100">
                  {wrong.question.options.map((opt, optIdx) => {
                    let optClass = "text-slate-500 py-3 px-5 rounded-xl bg-slate-50 font-medium";
                    if (optIdx === wrong.question.correctAnswer) optClass = "bg-emerald-50 text-emerald-700 font-bold py-3 px-5 rounded-xl flex items-center gap-2 border-2 border-emerald-200 shadow-sm";
                    else if (optIdx === wrong.userAnswer) optClass = "bg-rose-50 text-rose-500 line-through py-3 px-5 rounded-xl flex items-center gap-2 border-2 border-rose-100 opacity-80";

                    return (
                      <div key={optIdx} className={optClass}>
                        {opt}
                        {optIdx === wrong.question.correctAnswer && <CheckCircle2 className="w-5 h-5 ml-auto" />}
                        {optIdx === wrong.userAnswer && <XCircle className="w-5 h-5 ml-auto" />}
                      </div>
                    );
                  })}
                </div>

                {wrong.question.explanation && (
                  <div className="bg-gradient-to-br from-rose-50 to-pink-50 text-rose-900 p-6 rounded-2xl text-base leading-relaxed border border-rose-100 shadow-inner">
                    <strong className="flex items-center gap-2 mb-3 text-rose-800 text-lg"><AlertCircle className="w-5 h-5"/> 解析：</strong>
                    <span className="whitespace-pre-wrap font-medium">{wrong.question.explanation}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // 答题界面
  if (!currentQuestion) return null;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center py-6 sm:py-10 px-4 sm:px-6">
      <style>{customStyles}</style>

      <div className="w-full max-w-4xl mb-8">
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={() => setGameState('home')}
            className="flex items-center gap-2 text-slate-500 hover:text-rose-500 transition-colors font-bold text-sm bg-white px-4 py-2 rounded-xl shadow-sm border border-slate-200"
          >
            <RotateCcw className="w-4 h-4" /> 退出
          </button>

          <div className="flex items-center gap-4 bg-white px-5 py-2 rounded-2xl shadow-sm border border-slate-100">
            <div className="text-lg font-black text-slate-700">得分: <span className="text-rose-500">{score}</span></div>
            {streak > 1 && (
              <div className="flex items-center text-white font-black bg-gradient-to-r from-amber-400 to-orange-500 px-3 py-1 rounded-xl shadow-md animate-bounce">
                <Flame className="w-5 h-5 mr-1" />
                {streak} 连击
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-4 px-2 gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="bg-slate-800 text-white px-4 py-1.5 rounded-lg text-sm font-bold shadow-md truncate max-w-[200px]">{activeExamData.title}</span>
            <span className="bg-white text-slate-700 px-4 py-1.5 rounded-lg text-sm font-bold shadow-sm border border-slate-200">{currentQuestion.chapter}</span>
            <span className="text-sm font-black text-slate-400 ml-2">进度 {currentQuestionIndex + 1} / {filteredData.length}</span>
          </div>
        </div>

        <div className="h-5 w-full bg-slate-200/60 rounded-full overflow-hidden shadow-inner p-1">
          <div
            className="h-full bg-gradient-to-r from-rose-400 to-pink-500 rounded-full transition-all duration-500 ease-out relative shadow-sm"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute top-0 left-0 right-0 bottom-0 bg-white/20" style={{ backgroundImage: 'linear-gradient(45deg, rgba(255,255,255,.15) 25%, transparent 25%, transparent 50%, rgba(255,255,255,.15) 50%, rgba(255,255,255,.15) 75%, transparent 75%, transparent)', backgroundSize: '1.5rem 1.5rem' }}></div>
          </div>
        </div>
      </div>

      <div className={`w-full max-w-4xl flex-1 flex flex-col ${shake ? 'animate-shake' : ''}`}>
        <div className="bg-white p-8 sm:p-12 rounded-[2rem] mb-6 shadow-xl border border-slate-100 relative overflow-hidden">
          {getStreakMessage() && !isAnswered && (
            <div className="absolute top-0 right-0 bg-gradient-to-bl from-amber-400 to-orange-500 text-white px-8 py-3 rounded-bl-3xl text-sm font-black shadow-lg tracking-widest z-20">
              {getStreakMessage()}
            </div>
          )}

          <h2 className="text-2xl sm:text-3xl font-bold text-slate-800 leading-relaxed mb-10 flex gap-4">
            <span className="text-rose-500 font-black text-4xl leading-none">Q.</span>
            {currentQuestion.question}
          </h2>

          <div className="space-y-4">
            {currentQuestion.options.map((option, index) => {
              let buttonStyle = "bg-slate-50 border-2 border-transparent text-slate-700 hover:border-rose-400 hover:bg-rose-50 hover:shadow-md";
              let icon = null;

              if (isAnswered) {
                if (index === currentQuestion.correctAnswer) {
                  buttonStyle = "bg-emerald-50 border-2 border-emerald-500 text-emerald-800 z-10 scale-[1.02] shadow-xl transition-transform";
                  icon = <CheckCircle2 className="w-8 h-8 text-emerald-600 flex-shrink-0" />;
                } else if (index === selectedOption) {
                  buttonStyle = "bg-rose-50 border-2 border-rose-300 text-rose-500 opacity-60";
                  icon = <XCircle className="w-8 h-8 text-rose-400 flex-shrink-0" />;
                } else {
                  buttonStyle = "bg-slate-50 border-2 border-slate-100 text-slate-400 opacity-30";
                }
              }

              return (
                <button
                  key={index}
                  disabled={isAnswered}
                  onClick={() => handleOptionClick(index)}
                  className={`w-full text-left p-6 rounded-2xl flex items-center justify-between transition-all duration-200 outline-none font-bold text-lg ${buttonStyle}`}
                >
                  <span className="pr-4 leading-relaxed">{option}</span>
                  {icon}
                </button>
              );
            })}
          </div>
        </div>

        <div className={`transition-all duration-500 ease-in-out ${isAnswered ? 'opacity-100 translate-y-0 h-auto' : 'opacity-0 translate-y-4 h-0 overflow-hidden'}`}>
          <div className="bg-white p-8 sm:p-10 rounded-3xl mb-10 flex flex-col gap-8 border-l-8 border-l-rose-500 shadow-2xl relative">
            <div className="absolute top-0 right-0 w-32 h-32 bg-rose-50 rounded-bl-full -z-10"></div>
            <div className="z-10">
              <h3 className="text-2xl font-black text-rose-900 mb-4 flex items-center gap-3">
                <BookOpen className="w-7 h-7 text-rose-600"/> 解析
              </h3>
              <p className="text-slate-700 text-lg leading-relaxed font-bold bg-rose-50/50 p-6 rounded-2xl border border-rose-100">
                {currentQuestion.explanation || '暂无解析'}
              </p>
            </div>

            <div className="flex items-center justify-end w-full pt-6 border-t border-slate-100 z-10">
              <button
                onClick={handleNext}
                className="bg-slate-900 hover:bg-black text-white font-black py-4 px-10 rounded-2xl shadow-xl hover:shadow-2xl transition-all flex items-center justify-center gap-3 transform hover:translate-x-1 text-lg"
              >
                {currentQuestionIndex < filteredData.length - 1 ? '进入下一题' : '结束并结算'}
                <ArrowRight className="w-6 h-6" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
