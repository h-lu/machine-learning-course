#!/usr/bin/env python3
"""Rebuild lesson 09's two teaching figures (no model/data downloads).
Run: MPLCONFIGDIR=/tmp/lesson09-mpl python3 course-student-template/lesson-09/figures/render_figures.py
Requires Python 3, NumPy and Matplotlib; a CJK font (default: Noto Sans CJK JP).
Override font with LESSON09_FONT. SVG text is embedded as paths for portable Chinese.
"""
from pathlib import Path
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

OUT = Path(__file__).resolve().parent
plt.rcParams.update({'font.family': os.getenv('LESSON09_FONT', 'Noto Sans CJK JP'),
                     'font.size': 15, 'axes.titlesize': 18, 'axes.labelsize': 15,
                     'xtick.labelsize': 13, 'ytick.labelsize': 13,
                     'svg.fonttype': 'path', 'svg.hashsalt': 'lesson09-teaching-figures',
                     'axes.unicode_minus': False, 'figure.facecolor': 'white'})
INK = '#253247'; BLUE = '#176594'; ORANGE = '#a85716'; RED = '#b32842'
LEAF_COLORS = ['#d6e8f3', '#ffe3b5', '#dcebdd']

def save(fig, name):
    fig.savefig(OUT / (name+'.svg'), metadata={'Date': None})
    svg = OUT / (name+'.svg')
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    fig.savefig(OUT / (name+'.png'), dpi=200, metadata={'Software': 'Matplotlib'})
    plt.close(fig)

def comparison():
    x = np.array([0., 1., 1., 2.]); y = np.array([1., 2., 4., 5.])
    b, w = np.linalg.lstsq(np.column_stack([np.ones(4), x]), y, rcond=None)[0]
    tree = lambda v: np.where(np.asarray(v)<=.5, 1., np.where(np.asarray(v)<=1.5, 3., 5.))
    assert np.allclose([b, w], [1, 2])
    assert np.allclose(b+w*x, tree(x))
    assert np.allclose(tree([.5, .500001, 1.5, 1.500001]), [1,3,3,5])
    assert np.isclose(b+w*1.2,3.4) and tree(1.2)==3
    fig, axes = plt.subplots(1,2,figsize=(12,6.2),sharex=True,sharey=True)
    fig.subplots_adjust(left=.075,right=.975,bottom=.22,top=.80,wspace=.15)
    fig.suptitle('同一组记录：直线预测与分段预测', fontsize=22, y=.97, color=INK)
    fig.text(.5,.87,'● 黑点：实际耗时     ★ 红星：1.2 MB 新文件的预测（真实耗时未知）',ha='center',fontsize=14)
    for ax in axes:
        ax.set(xlim=(-.13,2.25),ylim=(.45,5.9),xticks=[0,.5,1,1.5,2],yticks=[1,2,3,4,5],xlabel='文件大小 x（MB）')
        ax.grid(axis='y',color='#e2e6eb',lw=.8)
        ax.set_axisbelow(True)
        ax.spines[['top','right']].set_visible(False)
        ax.axvline(1.2,color='#9ca6af',ls=':',lw=1.5,zorder=1)
        ax.scatter(x,y,s=80,c=INK,edgecolors='white',linewidths=1,zorder=5)
    axes[0].set_ylabel('耗时 y（秒）')
    axes[0].set_title('最小二乘法（OLS）',pad=12,color=BLUE)
    xx=np.linspace(0,2.25,100)
    axes[0].plot(xx,b+w*xx,color=BLUE,lw=3,zorder=2)
    axes[0].text(.12,5.25,'预测 = 1 + 2x',color=BLUE,fontsize=16)
    axes[1].set_title('回归树（regression tree）',pad=12,color=ORANGE)
    for lo,hi,v in [(0,.5,1),(.5,1.5,3),(1.5,2.25,5)]:
        axes[1].plot([lo,hi],[v,v],color=ORANGE,lw=3,zorder=2)
    for threshold,lower,upper in [(.5,1,3),(1.5,3,5)]:
        axes[1].scatter([threshold],[lower],s=70,facecolors=ORANGE,edgecolors=ORANGE,zorder=4)
        axes[1].scatter([threshold],[upper],s=70,facecolors='white',edgecolors=ORANGE,lw=2,zorder=4)
    for ax,v in zip(axes,[3.4,3]):
        ax.scatter([1.2],[v],marker='*',s=240,c=RED,edgecolors='white',lw=.7,zorder=6)
        ax.annotate(f'{v:g} 秒',xy=(1.2,v),xytext=(1.65,2.05),color=RED,fontsize=17,
                    arrowprops={'arrowstyle':'->','color':RED,'lw':1.5})
    fig.text(.5,.105,'训练记录上的预测都为 1、3、3、5 秒；新点 x = 1.2 时，分别为 3.4 秒和 3 秒。',ha='center',fontsize=14)
    fig.text(.5,.045,'树的分界：实心端点包含等号（≤），空心端点不包含等号（>）。',ha='center',fontsize=14,color=INK)
    save(fig,'ols-vs-tree')

def partition():
    # Artificial rules, not fitted to the four observations or the bike data.
    predict=lambda x,c: 2 if x<=10 else (6 if c<=50 else 10)
    assert [predict(10,80),predict(10.001,50),predict(15,50.001),predict(15,30)]==[2,6,10,6]
    fig=plt.figure(figsize=(12,7.5))
    fig.suptitle('一棵树，两种读法：顺着条件走，也是在平面中找区域',fontsize=21,y=.98,color=INK)
    fig.text(.5,.92,'人工二维示意：预测文件传送耗时；未用前面四条记录或共享单车数据拟合。',ha='center',fontsize=14)
    treeax=fig.add_axes([.025,.23,.49,.61]); treeax.axis('off');treeax.set(xlim=(0,1),ylim=(0,1))
    ax=fig.add_axes([.615,.265,.35,.52])
    treeax.text(.5,1,'树结构：P 沿粗箭头到叶节点 B',ha='center',fontsize=16,color=INK)
    root=(.43,.84); mid=(.72,.50); a=(.15,.50); b=(.55,.14); c=(.90,.14)
    def node(pos,label,face='white',edge=INK):
        treeax.text(*pos,label,ha='center',va='center',fontsize=14,
                    bbox=dict(boxstyle='round,pad=.55',fc=face,ec=edge,lw=1.6),zorder=4)
    def edge(start,end,label,tx,ty,active=False):
        treeax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',lw=3 if active else 1.5,color=ORANGE if active else '#677587',shrinkA=35,shrinkB=38),zorder=1)
        treeax.text(tx,ty,label,ha='center',fontsize=13,color=ORANGE if active else INK,
                    bbox=dict(fc='white',ec='none',pad=1),zorder=2)
    edge(root,a,'≤ 10 MB',.16,.72)
    edge(root,mid,'> 10 MB',.74,.73,True)
    edge(mid,b,'≤ 50 分',.49,.33,True)
    edge(mid,c,'> 50 分',.90,.33)
    node(root,'根节点\n文件大小 x ≤ 10 MB？')
    node(mid,'拥挤程度 c ≤ 50 分？')
    node(a,'A\n预测 2 秒',LEAF_COLORS[0])
    node(b,'B\n预测 6 秒',LEAF_COLORS[1],ORANGE)
    node(c,'C\n预测 10 秒',LEAF_COLORS[2])
    for xy,width,height,col in [((0,0),10,100,LEAF_COLORS[0]),((10,0),10,50,LEAF_COLORS[1]),((10,50),10,50,LEAF_COLORS[2])]:
        ax.add_patch(Rectangle(xy,width,height,fc=col,ec='none',zorder=0))
    ax.axvline(10,color=INK,lw=2.2)
    ax.plot([10,20],[50,50],color=INK,lw=2.2)
    ax.set(xlim=(0,20),ylim=(0,100),xticks=[0,10,15,20],yticks=[0,30,50,100],xlabel='文件大小 x（MB）',ylabel='网络拥挤程度 c（分）')
    ax.set_title('特征平面：P 落在区域 B',fontsize=16,pad=20,color=INK)
    ax.text(5,53,'A\n预测 2 秒',ha='center',va='center',fontsize=16)
    ax.text(15,77,'C\n预测 10 秒',ha='center',va='center',fontsize=16)
    ax.text(15,12,'B：预测 6 秒',ha='center',fontsize=15)
    ax.scatter([15],[30],s=170,marker='*',c=RED,zorder=5)
    ax.text(15.8,31,'P',color=RED,fontsize=17,va='center')
    fig.text(.5,.165,'P：文件大小 15 MB，拥挤程度 30 分 → 先走 > 10，再走 ≤ 50 → 预测 6 秒。',ha='center',fontsize=15,color=INK)
    fig.text(.5,.102,'边界归属：x = 10 属于 A；在 x > 10 的部分，c = 50 属于 B。',ha='center',fontsize=14)
    fig.text(.5,.047,'拥挤程度为人工设定的 0–100 分：分数越高越拥挤。A、B、C 的颜色与叶节点一一对应。',ha='center',fontsize=13)
    save(fig,'tree-feature-partition')

if __name__=='__main__':
    comparison(); partition()
    print('Generated 2 SVG + 2 PNG; OLS, predictions and boundary checks passed.')
