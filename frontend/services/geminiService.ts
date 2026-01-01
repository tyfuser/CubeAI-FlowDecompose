
import { GoogleGenAI, Type } from "@google/genai";
import { Shot, VideoAnalysis, TargetPlatform, SlideData } from "../types";

// 简单的延迟函数
const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

// 带重试机制的调用函数
async function callGeminiWithRetry(fn: () => Promise<any>, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error: any) {
      const isQuotaError = error.message?.includes('429') || error.message?.includes('RESOURCE_EXHAUSTED');
      if (isQuotaError && i < maxRetries - 1) {
        // 指数退避：1s, 2s, 4s
        await delay(Math.pow(2, i) * 1000);
        continue;
      }
      throw error;
    }
  }
}

export const analyzeVideoConcept = async (input: string) => {
  return callGeminiWithRetry(async () => {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: `作为短视频营销策略专家和多模态视觉分析师，请深入拆解以下视频。
      
      分析要求：
      1. 使用中文进行回答。
      2. 深入剖析其“爆款基因”（Viral Genes）。
      3. 详细拆解前3秒钩子。
      4. 输出一份【评估报告】：包含 1-5 星的爆款匹配度、3 条核心优势分析、3 条可复用要点总结。
      5. 特别要求：请对该视频进行【六维优势评估】，各维度分值为 1-100。维度包括：钩子强度、情绪张力、视觉冲击、叙事逻辑、转化潜力、创新指数。
      
      目标输入：${input}`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            title: { type: Type.STRING },
            viralFactors: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  category: { type: Type.STRING },
                  description: { type: Type.STRING },
                  intensity: { type: Type.NUMBER }
                },
                required: ["category", "description", "intensity"]
              }
            },
            radarData: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  subject: { type: Type.STRING },
                  value: { type: Type.NUMBER },
                  fullMark: { type: Type.NUMBER, default: 100 }
                },
                required: ["subject", "value"]
              }
            },
            evaluationReport: {
              type: Type.OBJECT,
              properties: {
                starRating: { type: Type.NUMBER },
                coreStrengths: { type: Type.ARRAY, items: { type: Type.STRING } },
                reusablePoints: { type: Type.ARRAY, items: { type: Type.STRING } }
              },
              required: ["starRating", "coreStrengths", "reusablePoints"]
            },
            narrativeStructure: { type: Type.STRING },
            hookScore: { type: Type.NUMBER },
            hookDetails: {
              type: Type.OBJECT,
              properties: {
                visual: { type: Type.STRING },
                audio: { type: Type.STRING },
                text: { type: Type.STRING }
              },
              required: ["visual", "audio", "text"]
            },
            editingStyle: {
              type: Type.OBJECT,
              properties: {
                pacing: { type: Type.STRING },
                transitionType: { type: Type.STRING },
                colorPalette: { type: Type.STRING }
              },
              required: ["pacing", "transitionType", "colorPalette"]
            },
            audienceResponse: {
              type: Type.OBJECT,
              properties: {
                sentiment: { type: Type.STRING },
                keyTriggers: { type: Type.ARRAY, items: { type: Type.STRING } }
              },
              required: ["sentiment", "keyTriggers"]
            }
          },
          required: ["title", "viralFactors", "radarData", "evaluationReport", "narrativeStructure", "hookScore", "hookDetails", "editingStyle", "audienceResponse"]
        }
      }
    });

    return JSON.parse(response.text);
  });
};

export const generateCreativeScript = async (concept: string, strategy: string, platform: TargetPlatform = 'douyin'): Promise<Shot[]> => {
  return callGeminiWithRetry(async () => {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    
    const platformPrompts = {
      douyin: "重点关注【黄金3秒】钩子，节奏极快，多用反转，台词要口语化、情绪化，增加热门BGM卡点提示。",
      red: "重点关注【精致感与种草感】，台词中自动加入大量适合小红书的 Emoji，增加封面标题（SEO关键词）设计建议。",
      bilibili: "重点关注【信息深度与弹幕互动】，增加引导三连、前方高能等互动点提示，台词可以更专业、幽默，时长可适当拉长。"
    };

    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview',
      contents: `基于核心概念： "${concept}"，采用创作策略： "${strategy}"。
      
      目标平台：${platform}。
      平台特化要求：${platformPrompts[platform]}
      
      请生成详细的分镜脚本。要求全中文。`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              id: { type: Type.NUMBER },
              startTime: { type: Type.NUMBER },
              duration: { type: Type.NUMBER },
              type: { type: Type.STRING },
              description: { type: Type.STRING },
              dialogue: { type: Type.STRING },
              transition: { type: Type.STRING },
              platformSpecific: {
                type: Type.OBJECT,
                properties: {
                  platform: { type: Type.STRING },
                  tip: { type: Type.STRING }
                }
              }
            },
            required: ["id", "startTime", "duration", "type", "description", "dialogue", "transition"]
          }
        }
      }
    });

    return JSON.parse(response.text);
  });
};

/**
 * 重新生成幻灯片单页摘要
 */
export const regenerateSlideSummary = async (slideTitle: string, currentSummary: string): Promise<string> => {
  return callGeminiWithRetry(async () => {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: `你是一位专业的短视频分析师和幻灯片内容架构师。
      当前幻灯片标题是：“${slideTitle}”。
      原有的摘要内容是：“${currentSummary}”。
      
      请重新写一段 50-100 字的逻辑摘要。
      要求：
      1. 洞察深刻，解释该环节在视频爆款逻辑中的作用。
      2. 语气专业，适合作为 PPT 内容。
      3. 重点突出，语言凝练。`,
      config: {
        systemInstruction: "你只返回摘要正文，不要有任何多余的开场白或解释。"
      }
    });
    return response.text || currentSummary;
  });
};
