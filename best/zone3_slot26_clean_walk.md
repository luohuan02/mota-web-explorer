# 三区 slot26 clean walk（8次攻防，39F中途买DEF）

## 结论
- 主线状态：`HP=556 ATK=170 DEF=198 YK=3 BK=0 RK=0 G=926 MT40 x6y1 dmg=7293 door=42/4/1 shop=10`
- simple_stock_score(1YK=50HP=100G)：`1169.0`
- remaining_simple_value(31-40F)：`17891`
- errors/warnings：`0` / `0`

## 对照状态
- 7买，boss后停40F上楼口：`HP=224 ATK=170 DEF=182 YK=3 BK=0 RK=0 G=1846 MT40 x6y1 dmg=7625 door=42/4/1 shop=9`，simple=`1297.0`，errors=`0`
- 8买DEF，39F红宝石后回商店：`HP=556 ATK=170 DEF=198 YK=3 BK=0 RK=0 G=926 MT40 x6y1 dmg=7293 door=42/4/1 shop=10`，simple=`1169.0`，errors=`0`
- 8买ATK，39F红宝石后回商店：`HP=468 ATK=178 DEF=182 YK=3 BK=0 RK=0 G=926 MT40 x6y1 dmg=7381 door=42/4/1 shop=10`，simple=`1081.0`，errors=`0`

## 关键顺序
- 34F中间8怪和奖励必须在第一次从33F进入34F上侧时处理，不能等飞回34F后再做。
- 第2把蓝钥匙取MT32 x11y7，否则37F蓝门和39F谜题蓝门不够。
- 第8次属性购买放在39F x11y6红宝石后；此时G=961，够花920买DEF，并且中心对称飞行器还没使用，可以回39F继续进40F。
- 40F先主动清12怪，再触发x6y7事件，boss后只取钥匙和宝石，不取血瓶，停MT40 x6y1。

## 详细Walk
001. MT14 x6y10 飞行
002. MT14 x7y4 开门 yellowDoor [YK 4->3]
003. MT14 x7y2 击杀 zombieKnight [HP 1249->1137, G 176->206]
004. MT14 x7y1 拾取 redPotion [HP 1137->1237]
005. MT14 x6y1 拾取 yellowKey [YK 3->4]
006. MT14 x5y1 拾取 blueGem [DEF 64->66]
007. MT31 x6y2 飞行
008. MT31 x6y8 击杀 zombieKnight [HP 1237->1129, G 206->236]
009. MT31 x6y9 击杀 zombieKnight [HP 1129->1021, G 236->266]
010. MT31 x6y11 通过 upFloor
011. MT32 x6y11 换层
012. MT32 x6y10 到达
013. MT32 x6y10 事件战斗 yellowKnight [HP 1021->601, G 266->366]
014. MT32 x10y10 对话 blueShop
015. MT32 x10y10 商店 atk [ATK 76->84, G 366->286]
016. MT32 x10y10 商店 atk [ATK 84->92, G 286->146]
017. MT15 x6y2 飞行
018. MT15 x11y6 击杀 redPriest [HP 601->572, G 146->168]
019. MT15 x11y8 拾取 bluePotion [HP 572->972]
020. MT18 x6y2 飞行
021. MT18 x10y7 击杀 rock [G 168->196]
022. MT18 x11y8 开门 yellowDoor [YK 4->3]
023. MT18 x11y9 击杀 redPriest [HP 972->943, G 196->218]
024. MT18 x10y10 拾取 yellowKey [YK 3->4]
025. MT18 x10y11 拾取 blueGem [DEF 66->68]
026. MT19 x1y2 飞行
027. MT19 x7y6 击杀 rock [G 218->246]
028. MT19 x8y3 击杀 zombieKnight [HP 943->891, G 246->276]
029. MT19 x8y1 拾取 blueKey [BK 0->1]
030. MT14 x6y10 飞行
031. MT14 x1y7 开门 yellowDoor [YK 4->3]
032. MT14 x1y9 击杀 redPriest [HP 891->864, G 276->298]
033. MT14 x1y11 拾取 blueKey [BK 1->2]
034. MT17 x5y11 飞行
035. MT17 x10y10 开门 yellowDoor [YK 3->2]
036. MT17 x9y8 击杀 zombie [HP 864->847, G 298->316]
037. MT17 x11y8 击杀 zombie [HP 847->830, G 316->334]
038. MT17 x9y5 击杀 zombieKnight [HP 830->778, G 334->364]
039. MT17 x11y5 击杀 zombieKnight [HP 778->726, G 364->394]
040. MT17 x9y3 拾取 yellowKey [YK 2->3]
041. MT17 x9y1 拾取 redGem [ATK 92->94]
042. MT17 x11y1 拾取 blueGem [DEF 68->70]
043. MT17 x11y3 拾取 yellowKey [YK 3->4]
044. MT28 x10y11 飞行
045. MT28 x8y4 对话 specialTrader
046. MT28 x8y4 merchant sellYK [YK 4->3, G 394->494]
047. MT28 x8y4 merchant sellYK [YK 3->2, G 494->594]
048. MT32 x6y11 飞行
049. MT32 x10y10 对话 blueShop
050. MT32 x10y10 商店 atk [ATK 94->102, G 594->374]
051. MT32 x10y10 商店 atk [ATK 102->110, G 374->54]
052. MT32 x11y1 通过 upFloor
053. MT33 x10y1 换层
054. MT33 x7y1 开门 yellowDoor [YK 2->1]
055. MT33 x6y1 击杀 slimeMan [HP 726->516, G 54->84]
056. MT33 x5y2 拾取 redPotion [HP 516->716]
057. MT33 x6y3 拾取 yellowKey [YK 1->2]
058. MT33 x8y2 开门 yellowDoor [YK 2->1]
059. MT33 x11y3 拾取 bluePotion [HP 716->1516]
060. MT33 x10y5 到达
061. MT33 x10y5 事件 swordTrap
062. MT33 x9y5 击杀 ghostSkeleton [HP 1516->1296, G 84->119]
063. MT33 x11y5 击杀 ghostSkeleton [HP 1296->1076, G 119->154]
064. MT33 x9y7 击杀 soldier [HP 1076->556, G 154->199]
065. MT33 x11y7 击杀 soldier [HP 556->36, G 199->244]
066. MT33 x10y10 拾取 sword3 [ATK 110->150]
067. MT14 x6y10 飞行
068. MT14 x9y6 到达
069. MT20 x6y10 飞行
070. MT20 x8y11 击杀 redPriest [G 244->266]
071. MT20 x11y11 拾取 redPotion [HP 36->136]
072. MT20 x11y9 开门 yellowDoor [YK 1->0]
073. MT20 x10y8 击杀 bat [G 266->269]
074. MT20 x10y6 开门 blueDoor [BK 2->1]
075. MT20 x11y5 拾取 yellowKey [YK 0->1]
076. MT20 x11y4 拾取 bluePotion [HP 136->536]
077. MT2 x1y10 飞行
078. MT2 x3y1 开门 blueDoor [BK 1->0]
079. MT2 x6y2 击杀 blueGuard [HP 536->316, G 269->319]
080. MT2 x8y2 击杀 blueGuard [HP 316->96, G 319->369]
081. MT2 x3y5 拾取 yellowKey [YK 1->2]
082. MT2 x3y4 拾取 yellowKey [YK 2->3]
083. MT2 x4y4 拾取 yellowKey [YK 3->4]
084. MT2 x11y4 对话 oldman
085. MT2 x11y4 事件奖励 oldman [G 369->1369]
086. MT2 x10y11 对话 thief
087. MT2 x10y11 事件 thief
088. MT14 x11y10 飞行
089. MT14 x10y4 击杀 zombieKnight [HP 96->46, G 1369->1399]
090. MT14 x10y3 开门 yellowDoor [YK 4->3]
091. MT14 x9y1 拾取 yellowKey [YK 3->4]
092. MT14 x10y1 拾取 yellowKey [YK 4->5]
093. MT14 x11y1 拾取 yellowKey [YK 5->6]
094. MT14 x11y2 拾取 yellowKey [YK 6->7]
095. MT32 x6y11 飞行
096. MT32 x10y10 对话 blueShop
097. MT32 x10y10 商店 def [DEF 70->86, G 1399->959]
098. MT32 x10y10 商店 def [DEF 86->102, G 959->379]
099. MT2 x1y10 飞行
100. MT2 x3y11 拾取 bluePotion [HP 46->246]
101. MT2 x3y10 拾取 bluePotion [HP 246->446]
102. MT31 x6y2 飞行
103. MT31 x10y6 击杀 ghostSkeleton [HP 446->368, G 379->414]
104. MT31 x11y7 开门 yellowDoor [YK 7->6]
105. MT31 x9y8 开门 yellowDoor [YK 6->5]
106. MT31 x8y8 拾取 bluePotion [HP 368->1168]
107. MT32 x6y11 飞行
108. MT32 x7y3 开门 yellowDoor [YK 5->4]
109. MT32 x8y4 击杀 ghostSkeleton [HP 1168->1090, G 414->449]
110. MT32 x9y5 开门 yellowDoor [YK 4->3]
111. MT32 x11y5 拾取 yellowKey [YK 3->4]
112. MT32 x11y4 拾取 bluePotion [HP 1090->1890]
113. MT17 x6y2 飞行
114. MT17 x10y2 拾取 bluePotion [HP 1890->2290]
115. MT32 x6y11 飞行
116. MT32 x11y4 到达
117. MT32 x10y4 拾取 yellowKey [YK 4->5]
118. MT32 x8y7 击杀 redKnight [HP 2290->1906, G 449->514]
119. MT32 x9y8 开门 yellowDoor [YK 5->4]
120. MT32 x11y8 拾取 yellowKey [YK 4->5]
121. MT32 x11y7 拾取 blueKey [BK 0->1]
122. MT31 x6y10 飞行
123. MT31 x10y9 击杀 slimeMan [HP 1906->1830, G 514->544]
124. MT31 x9y10 拾取 yellowKey [YK 5->6]
125. MT31 x8y10 拾取 yellowKey [YK 6->7]
126. MT31 x8y11 拾取 yellowKey [YK 7->8]
127. MT31 x9y10 到达
128. MT31 x9y11 拾取 yellowKey [YK 8->9]
129. MT31 x2y6 击杀 ghostSkeleton [HP 1830->1752, G 544->579]
130. MT31 x1y5 开门 yellowDoor [YK 9->8]
131. MT31 x1y2 击杀 swordsman [G 579->634]
132. MT31 x3y1 拾取 yellowKey [YK 8->9]
133. MT31 x4y1 拾取 yellowKey [YK 9->10]
134. MT31 x3y2 拾取 yellowKey [YK 10->11]
135. MT31 x4y2 拾取 yellowKey [YK 11->12]
136. MT31 x3y4 开门 yellowDoor [YK 12->11]
137. MT31 x4y4 拾取 blueKey [BK 1->2]
138. MT33 x10y1 飞行
139. MT33 x4y1 击杀 zombieKnight [HP 1752->1734, G 634->664]
140. MT33 x3y1 开门 yellowDoor [YK 11->10]
141. MT33 x1y1 通过 upFloor
142. MT34 x2y1 换层
143. MT34 x2y3 击杀 slimeMan [HP 1734->1658, G 664->694]
144. MT34 x2y4 开门 yellowDoor [YK 10->9]
145. MT34 x5y5 开门 yellowDoor [YK 9->8]
146. MT34 x5y4 击杀 greenSlime [G 694->695]
147. MT34 x7y5 开门 yellowDoor [YK 8->7]
148. MT34 x7y4 击杀 swordsman [G 695->750]
149. MT34 x9y5 开门 yellowDoor [YK 7->6]
150. MT34 x9y4 击杀 blackSlime [G 750->758]
151. MT34 x11y5 开门 yellowDoor [YK 6->5]
152. MT34 x11y4 击杀 soldier [HP 1658->1462, G 758->803]
153. MT34 x11y7 开门 yellowDoor [YK 5->4]
154. MT34 x11y8 击杀 bat [G 803->806]
155. MT34 x9y7 开门 yellowDoor [YK 4->3]
156. MT34 x9y8 击杀 redKnight [HP 1462->1078, G 806->871]
157. MT34 x7y7 开门 yellowDoor [YK 3->2]
158. MT34 x7y8 击杀 redSlime [G 871->873]
159. MT34 x5y7 开门 yellowDoor [YK 2->1]
160. MT34 x5y8 击杀 ghostSkeleton [HP 1078->1000, G 873->908]
161. MT34 x2y6 事件奖励 redKey
162. MT34 x2y6 拾取 redKey [RK 0->1]
163. MT34 x1y5 拾取 yellowKey [YK 1->2]
164. MT34 x3y5 拾取 yellowKey [YK 2->3]
165. MT34 x1y7 拾取 yellowKey [YK 3->4]
166. MT34 x3y7 拾取 yellowKey [YK 4->5]
167. MT34 x4y2 开门 yellowDoor [YK 5->4]
168. MT34 x5y2 击杀 slimeMan [HP 1000->924, G 908->938]
169. MT34 x6y1 拾取 yellowKey [YK 4->5]
170. MT34 x7y2 击杀 redKnight [HP 924->540, G 938->1003]
171. MT34 x8y2 开门 yellowDoor [YK 5->4]
172. MT34 x9y1 拾取 yellowKey [YK 4->5]
173. MT34 x10y1 拾取 yellowKey [YK 5->6]
174. MT34 x10y2 拾取 yellowKey [YK 6->7]
175. MT34 x11y1 拾取 blueGem [DEF 102->106]
176. MT34 x2y8 开门 yellowDoor [YK 7->6]
177. MT34 x3y9 击杀 ghostSkeleton [HP 540->466, G 1003->1038]
178. MT34 x4y10 开门 yellowDoor [YK 6->5]
179. MT34 x8y10 开门 yellowDoor [YK 5->4]
180. MT34 x9y10 击杀 soldier [HP 466->278, G 1038->1083]
181. MT34 x11y10 拾取 redPotion [HP 278->478]
182. MT34 x11y11 拾取 redGem [ATK 150->154]
183. MT34 x10y11 拾取 yellowKey [YK 4->5]
184. MT34 x6y11 通过 upFloor
185. MT35 x6y10 换层
186. MT35 x5y10 对话 thief
187. MT35 x5y10 事件 thief
188. MT35 x3y9 通过 fakeWall
189. MT35 x3y10 通过 fakeWall
190. MT35 x3y11 通过 fakeWall
191. MT35 x2y11 通过 fakeWall
192. MT35 x1y11 通过 fakeWall
193. MT35 x1y10 通过 fakeWall
194. MT35 x1y9 通过 fakeWall
195. MT35 x1y8 通过 fakeWall
196. MT35 x1y7 通过 fakeWall
197. MT35 x1y6 通过 fakeWall
198. MT35 x1y5 通过 fakeWall
199. MT35 x1y4 通过 fakeWall
200. MT35 x1y3 通过 fakeWall
201. MT35 x1y2 通过 fakeWall
202. MT35 x2y2 通过 fakeWall
203. MT35 x3y2 通过 fakeWall
204. MT35 x4y2 通过 fakeWall
205. MT35 x11y1 通过 upFloor
206. MT36 x11y2 换层
207. MT36 x11y3 击杀 slimeMan [HP 478->410, G 1083->1113]
208. MT36 x11y5 击杀 swordsman [G 1113->1168]
209. MT36 x11y7 击杀 redKnight [HP 410->38, G 1168->1233]
210. MT36 x11y11 通过 upFloor
211. MT37 x11y10 换层
212. MT34 x6y10 飞行
213. MT34 x1y10 击杀 swordsman [G 1233->1288]
214. MT34 x1y11 拾取 bluePotion [HP 38->838]
215. MT31 x6y10 飞行
216. MT32 x6y11 飞行
217. MT32 x10y10 对话 blueShop
218. MT32 x10y10 商店 def [DEF 106->122, G 1288->548]
219. MT37 x11y10 飞行
220. MT37 x9y11 击杀 ghostSkeleton [HP 838->780, G 548->583]
221. MT37 x3y11 击杀 slimeMan [HP 780->744, G 583->613]
222. MT37 x1y9 击杀 soldier [HP 744->588, G 613->658]
223. MT37 x1y6 拾取 redPotion [HP 588->788]
224. MT37 x1y3 开门 blueDoor [BK 2->1]
225. MT37 x1y1 通过 upFloor
226. MT38 x2y1 换层
227. MT38 x3y1 开门 redDoor [RK 1->0]
228. MT38 x4y1 击杀 slimeMan [HP 788->752, G 658->688]
229. MT38 x5y2 对话 trader
230. MT38 x5y2 商人 yellowKey [YK 5->8, G 688->488]
231. MT38 x6y2 拾取 yellowKey [YK 8->9]
232. MT38 x7y3 开门 yellowDoor [YK 9->8]
233. MT38 x7y6 击杀 ghostSkeleton [HP 752->694, G 488->523]
234. MT38 x7y7 击杀 swordsman [G 523->578]
235. MT38 x6y8 拾取 redPotion [HP 694->894]
236. MT38 x5y8 拾取 blueGem [DEF 122->126]
237. MT38 x8y1 击杀 slimeMan [HP 894->866, G 578->608]
238. MT38 x9y1 开门 yellowDoor [YK 8->7]
239. MT38 x11y3 开门 yellowDoor [YK 7->6]
240. MT38 x11y6 击杀 ghostSkeleton [HP 866->812, G 608->643]
241. MT38 x11y8 开门 yellowDoor [YK 6->5]
242. MT38 x11y9 击杀 ghostSkeleton [HP 812->758, G 643->678]
243. MT38 x9y9 拾取 yellowKey [YK 5->6]
244. MT38 x9y11 击杀 soldier [HP 758->610, G 678->723]
245. MT38 x8y11 开门 yellowDoor [YK 6->5]
246. MT38 x7y11 击杀 zombie [G 723->741]
247. MT38 x5y11 击杀 swordsman [G 741->796]
248. MT38 x4y11 开门 yellowDoor [YK 5->4]
249. MT38 x1y10 击杀 blueGuard [HP 610->502, G 796->846]
250. MT38 x3y10 击杀 blueGuard [HP 502->394, G 846->896]
251. MT38 x2y7 拾取 shield3 [DEF 126->166]
252. MT38 x11y11 拾取 bluePotion [HP 394->1194]
253. MT38 x11y1 通过 upFloor
254. MT39 x11y2 换层
255. MT39 x11y3 拾取 yellowKey [YK 4->5]
256. MT39 x10y4 开门 yellowDoor [YK 5->4]
257. MT39 x9y6 击杀 slimeMan [G 896->926]
258. MT39 x11y7 击杀 ghostSkeleton [HP 1194->1180, G 926->961]
259. MT39 x11y6 拾取 redGem [ATK 154->158]
260. MT31 x6y10 飞行
261. MT32 x6y11 飞行
262. MT32 x10y10 对话 blueShop
263. MT32 x10y10 商店 def [DEF 166->182, G 961->41]
264. MT38 x2y1 飞行
265. MT38 x11y1 到达
266. MT39 x11y2 换层
267. MT39 x10y8 开门 yellowDoor [YK 4->3]
268. MT39 x10y9 击杀 redKnight [HP 1180->1036, G 41->106]
269. MT39 x8y10 开门 yellowDoor [YK 3->2]
270. MT39 x6y11 击杀 slimeMan [G 106->136]
271. MT39 x4y10 开门 yellowDoor [YK 2->1]
272. MT39 x3y11 拾取 yellowKey [YK 1->2]
273. MT39 x2y10 击杀 ghostSkeleton [G 136->171]
274. MT39 x2y8 开门 blueDoor [BK 1->0]
275. MT39 x4y2 开门 yellowDoor [YK 2->1]
276. MT39 x6y4 开门 yellowDoor [YK 1->0]
277. MT39 x4y4 事件奖励 centerFly3
278. MT39 x4y4 拾取 centerFly3
279. MT39 x5y9 击杀 swordsman [G 171->226]
280. MT39 x6y9 拾取 blueGem [DEF 182->186]
281. MT39 x11y11 通过 upFloor
282. MT40 x10y11 换层
283. MT40 x2y1 事件 centerFly3
284. MT40 x2y2 击杀 swordsman [G 226->281]
285. MT40 x3y2 击杀 swordsman [G 281->336]
286. MT40 x4y2 击杀 swordsman [G 336->391]
287. MT40 x3y4 击杀 ghostSkeleton [G 391->426]
288. MT40 x4y4 击杀 ghostSkeleton [G 426->461]
289. MT40 x5y4 击杀 ghostSkeleton [G 461->496]
290. MT40 x7y4 击杀 soldier [HP 1036->1008, G 496->541]
291. MT40 x8y4 击杀 soldier [HP 1008->980, G 541->586]
292. MT40 x9y4 击杀 soldier [HP 980->952, G 586->631]
293. MT40 x8y2 击杀 redKnight [HP 952->820, G 631->696]
294. MT40 x9y2 击杀 redKnight [HP 820->688, G 696->761]
295. MT40 x10y2 击杀 redKnight [HP 688->556, G 761->826]
296. MT40 x6y7 到达
297. MT40 x6y7 事件奖励 yellowKnight [G 826->926]
298. MT40 x2y2 拾取 yellowKey [YK 0->1]
299. MT40 x3y2 拾取 yellowKey [YK 1->2]
300. MT40 x4y2 拾取 yellowKey [YK 2->3]
301. MT40 x8y2 拾取 redGem [ATK 158->162]
302. MT40 x9y2 拾取 redGem [ATK 162->166]
303. MT40 x10y2 拾取 redGem [ATK 166->170]
304. MT40 x7y4 拾取 blueGem [DEF 186->190]
305. MT40 x8y4 拾取 blueGem [DEF 190->194]
306. MT40 x9y4 拾取 blueGem [DEF 194->198]
307. MT40 x6y1 通过 upFloor
