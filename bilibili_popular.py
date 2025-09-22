import requests
import re
import json
import csv
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import os


class BilibiliPopularVideoAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0',
            'Referer': 'https://www.bilibili.com/'
        }

        # 尝试读取cookie
        try:
            if os.path.exists('cookie.token'):
                with open('cookie.token', 'r') as f:
                    self.headers['Cookie'] = f.read().strip()
                    print("✅ Cookie文件加载成功")
        except Exception as e:
            print(f"⚠️  警告: 无法读取cookie文件 ({e})，部分功能可能受限")

    def get_user_input(self):
        """
        交互式获取用户输入
        """
        print("🎯 B站热门视频分析工具")
        print("=" * 50)

        # 获取每页数量
        while True:
            try:
                page_size = input("📊 请输入每页视频数量 (默认50, 最大100): ").strip()
                if not page_size:
                    page_size = 50
                else:
                    page_size = int(page_size)

                if 1 <= page_size <= 100:
                    break
                else:
                    print("❌ 请输入1-100之间的数字")
            except ValueError:
                print("❌ 请输入有效的数字")

        # 获取起始页码
        while True:
            try:
                start_page = input("📄 请输入起始页码 (默认1): ").strip()
                if not start_page:
                    start_page = 1
                else:
                    start_page = int(start_page)

                if start_page >= 1:
                    break
                else:
                    print("❌ 页码必须大于等于1")
            except ValueError:
                print("❌ 请输入有效的数字")

        # 获取最大页数
        while True:
            try:
                max_pages = input("🔢 请输入要获取的页数 (默认1): ").strip()
                if not max_pages:
                    max_pages = 1
                else:
                    max_pages = int(max_pages)

                if max_pages >= 1:
                    break
                else:
                    print("❌ 页数必须大于等于1")
            except ValueError:
                print("❌ 请输入有效的数字")

        return page_size, start_page, max_pages

    def get_popular_videos(self, page_size: int = 50, page_number: int = 1, max_pages: int = 1) -> List[Dict[str, Any]]:
        """
        获取B站热门视频信息（支持多页获取）

        Args:
            page_size: 每页视频数量 (ps参数)
            page_number: 起始页码 (pn参数)
            max_pages: 最大获取页数

        Returns:
            List[Dict]: 热门视频信息列表
        """
        all_videos = []

        for page in range(page_number, page_number + max_pages):
            print(f"📄 正在获取第 {page} 页热门视频...")

            url = f'https://api.bilibili.com/x/web-interface/popular?ps={page_size}&pn={page}'

            try:
                response = self.session.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                data = response.json()

                if data['code'] != 0:
                    print(f"❌ 第 {page} 页API返回错误: {data['message']}")
                    break

                videos = data['data']['list']
                if not videos:
                    print(f"ℹ️  第 {page} 页没有更多视频")
                    break

                all_videos.extend(videos)
                print(f"✅ 第 {page} 页获取成功，共 {len(videos)} 个视频")

                # 添加延迟避免请求过快
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"❌ 获取第 {page} 页失败: {e}")
                break
            except Exception as e:
                print(f"❌ 解析第 {page} 页数据时出错: {e}")
                break

        return all_videos

    def get_video_details(self, bvid: str) -> Dict[str, Any]:
        """
        获取视频详细统计数据

        Args:
            bvid: 视频BV号

        Returns:
            Dict: 视频详细数据
        """
        # 方法1: 通过网页抓取
        stats = self._get_video_stats_from_web(bvid)

        # 方法2: 通过API获取更多数据
        api_data = self._get_video_stats_from_api(bvid)

        return {**stats, **api_data}

    def _get_video_stats_from_web(self, bvid: str) -> Dict[str, str]:
        """从网页获取视频统计数据"""
        url = f'https://www.bilibili.com/video/{bvid}'

        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            # 更健壮的正则表达式匹配
            patterns = [
                r"视频播放量 (\d+[,]?\d*)、弹幕量 (\d+[,]?\d*)、点赞数 (\d+[,]?\d*)、投硬币枚数 (\d+[,]?\d*)、收藏人数 (\d+[,]?\d*)、转发人数 (\d+[,]?\d*)",
                r"播放量 (\d+[,]?\d*).*弹幕量 (\d+[,]?\d*).*点赞数 (\d+[,]?\d*).*投硬币枚数 (\d+[,]?\d*).*收藏人数 (\d+[,]?\d*).*转发人数 (\d+[,]?\d*)"
            ]

            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return {
                        'play_count': match.group(1).replace(',', ''),
                        'danmaku_count': match.group(2).replace(',', ''),
                        'like_count': match.group(3).replace(',', ''),
                        'coin_count': match.group(4).replace(',', ''),
                        'favorite_count': match.group(5).replace(',', ''),
                        'share_count': match.group(6).replace(',', '')
                    }

            return {key: 'N/A' for key in ['play_count', 'danmaku_count', 'like_count',
                                           'coin_count', 'favorite_count', 'share_count']}

        except Exception as e:
            print(f"❌ 从网页获取视频数据失败 {bvid}: {e}")
            return {key: 'N/A' for key in ['play_count', 'danmaku_count', 'like_count',
                                           'coin_count', 'favorite_count', 'share_count']}

    def _get_video_stats_from_api(self, bvid: str) -> Dict[str, Any]:
        """通过API获取视频统计数据"""
        url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'

        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['code'] == 0:
                stat = data['data']['stat']
                return {
                    'view': stat.get('view', 0),
                    'danmaku': stat.get('danmaku', 0),
                    'like': stat.get('like', 0),
                    'coin': stat.get('coin', 0),
                    'favorite': stat.get('favorite', 0),
                    'share': stat.get('share', 0),
                    'reply': stat.get('reply', 0),
                    'duration': data['data'].get('duration', 0),
                    'pubdate': data['data'].get('pubdate', 0),
                    'cid': data['data'].get('cid', 0),
                    'tname': data['data'].get('tname', '')  # 分区名称
                }
            else:
                return {}

        except Exception as e:
            print(f"❌ 从API获取视频数据失败 {bvid}: {e}")
            return {}

    def format_duration(self, seconds: int) -> str:
        """格式化视频时长"""
        if seconds == 0:
            return 'N/A'

        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    def format_timestamp(self, timestamp: int) -> str:
        """格式化时间戳"""
        if timestamp == 0:
            return '未知'
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def format_number(self, number: Any) -> str:
        """格式化数字显示"""
        if number == 'N/A' or number is None:
            return 'N/A'
        try:
            num = int(number)
            return f"{num:,}"
        except:
            return str(number)

    def export_to_json(self, videos: List[Dict[str, Any]], filename: str = None):
        """导出数据到JSON文件"""
        if not filename:
            filename = f'bilibili_hot_videos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(videos, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON数据已导出到: {filename}")
        except Exception as e:
            print(f"❌ 导出JSON失败: {e}")

    def export_to_csv(self, videos: List[Dict[str, Any]], filename: str = None):
        """导出数据到CSV文件"""
        if not filename:
            filename = f'bilibili_hot_videos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        try:
            if videos:
                # 选择要导出的字段
                export_fields = [
                    'rank', 'title', 'owner_name', 'play_count', 'danmaku_count',
                    'like_count', 'coin_count', 'favorite_count', 'share_count',
                    'reply_count', 'duration_formatted', 'publish_time', 'bvid',
                    'pub_location', 'tname'
                ]

                # 过滤数据
                export_data = []
                for video in videos:
                    export_video = {field: video.get(field, '') for field in export_fields}
                    export_data.append(export_video)

                with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=export_fields)
                    writer.writeheader()
                    writer.writerows(export_data)

                print(f"✅ CSV数据已导出到: {filename}")
        except Exception as e:
            print(f"❌ 导出CSV失败: {e}")

    def generate_markdown_report(self, videos: List[Dict[str, Any]], filename: str = None):
        """生成Markdown格式的报告"""
        if not filename:
            filename = f'bilibili_hot_videos_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# 🎬 B站热门视频分析报告\n\n")
                f.write(f"## 📋 报告信息\n")
                f.write(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- **分析视频数**: {len(videos)} 个\n\n")

                # 汇总统计
                valid_plays = [int(v.get('play_count', 0)) for v in videos if str(v.get('play_count', '0')).isdigit()]
                total_views = sum(valid_plays) if valid_plays else 0
                avg_views = total_views // len(valid_plays) if valid_plays else 0

                f.write(f"## 📊 汇总统计\n")
                f.write(f"- **总播放量**: {self.format_number(total_views)}\n")
                f.write(f"- **平均播放量**: {self.format_number(avg_views)}\n")
                f.write(f"- **最高播放量**: {self.format_number(max(valid_plays)) if valid_plays else 'N/A'}\n")
                f.write(f"- **最低播放量**: {self.format_number(min(valid_plays)) if valid_plays else 'N/A'}\n\n")

                # 分区统计
                category_stats = {}
                for video in videos:
                    category = video.get('tname', '未知分区')
                    category_stats[category] = category_stats.get(category, 0) + 1

                f.write(f"## 🗂️ 分区分布\n")
                for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- **{category}**: {count} 个视频 ({count / len(videos) * 100:.1f}%)\n")
                f.write("\n")

                f.write(f"## 🎥 视频详情\n\n")
                for i, video in enumerate(videos, 1):
                    f.write(f"### {i}. {video['title']}\n\n")
                    f.write(f"**👤 UP主**: [{video['owner_name']}](https://space.bilibili.com/{video['owner_mid']})\n\n")
                    f.write(f"**📊 数据统计**:\n")
                    f.write(f"- 播放: {self.format_number(video.get('play_count', 'N/A'))} | ")
                    f.write(f"弹幕: {self.format_number(video.get('danmaku_count', 'N/A'))} | ")
                    f.write(f"点赞: {self.format_number(video.get('like_count', 'N/A'))}\n")
                    f.write(f"- 投币: {self.format_number(video.get('coin_count', 'N/A'))} | ")
                    f.write(f"收藏: {self.format_number(video.get('favorite_count', 'N/A'))} | ")
                    f.write(f"转发: {self.format_number(video.get('share_count', 'N/A'))}\n")
                    f.write(f"- 回复: {self.format_number(video.get('reply_count', 'N/A'))}\n\n")

                    f.write(f"📅 信息**:\n")
                    f.write(f"- 发布时间: {video.get('publish_time', '未知')}\n")
                    f.write(f"- 视频时长: {video.get('duration_formatted', '未知')}\n")
                    f.write(f"- 发布位置: {video.get('pub_location', '未知')}\n")
                    f.write(f"- 视频分区: {video.get('tname', '未知')}\n\n")

                    f.write(f"**🔗 链接**: [点击观看](https://www.bilibili.com/video/{video['bvid']})\n\n")
                    f.write(f"**🖼️ 封面**: ![{video['title'][:20]}]({video['pic']})\n\n")

                    if video.get('desc'):
                        f.write(f"**📝 简介**: {video.get('desc', '无')}\n\n")

                    f.write("---\n\n")

            print(f"✅ Markdown报告已生成: {filename}")

        except Exception as e:
            print(f"❌ 生成Markdown报告失败: {e}")

    def run_analysis(self):
        """运行完整分析"""
        print("🚀 开始获取B站热门视频信息...")
        print("=" * 60)

        # 获取用户输入
        page_size, start_page, max_pages = self.get_user_input()

        print("=" * 60)
        print(f"📋 参数设置: 每页 {page_size} 个视频，从第 {start_page} 页开始，获取 {max_pages} 页")
        print("=" * 60)

        # 获取热门视频
        videos = self.get_popular_videos(page_size, start_page, max_pages)

        if not videos:
            print("❌ 未能获取到热门视频数据")
            return

        print(f"\n✅ 成功获取到 {len(videos)} 个热门视频")
        print("正在获取详细统计数据...")
        print("=" * 60)

        enriched_videos = []

        for i, video in enumerate(videos, 1):
            print(f"🔍 正在处理第 {i}/{len(videos)} 个视频: {video['title'][:30]}...")

            # 获取详细数据
            details = self.get_video_details(video['bvid'])

            # 合并数据
            enriched_video = {
                'rank': i,
                'title': video['title'],
                'desc': video.get('desc', ''),
                'bvid': video['bvid'],
                'short_link': video.get('short_link_v2', ''),
                'pic': video.get('pic', ''),
                'first_frame': video.get('first_frame', ''),
                'pub_location': video.get('pub_location', ''),
                'owner_name': video['owner']['name'],
                'owner_mid': video['owner']['mid'],
                'owner_face': video['owner']['face'],
                'play_count': details.get('play_count', details.get('view', 'N/A')),
                'danmaku_count': details.get('danmaku_count', details.get('danmaku', 'N/A')),
                'like_count': details.get('like_count', details.get('like', 'N/A')),
                'coin_count': details.get('coin_count', details.get('coin', 'N/A')),
                'favorite_count': details.get('favorite_count', details.get('favorite', 'N/A')),
                'share_count': details.get('share_count', details.get('share', 'N/A')),
                'reply_count': details.get('reply', 'N/A'),
                'duration': details.get('duration', 0),
                'duration_formatted': self.format_duration(details.get('duration', 0)),
                'publish_time': self.format_timestamp(details.get('pubdate', 0)),
                'tname': details.get('tname', '未知'),
                'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            enriched_videos.append(enriched_video)

            self._display_video_info(enriched_video, i)

            # 添加延迟避免请求过快
            time.sleep(0.3)

        # 导出数据
        print("\n" + "=" * 60)
        print("📊 数据导出选项:")
        print("1. JSON格式 (完整数据)")
        print("2. CSV格式 (精简数据)")
        print("3. Markdown报告 (详细分析)")
        print("4. 全部导出")
        print("5. 不导出")

        choice = input("请选择导出格式 (1-5): ").strip()

        if choice in ['1', '4']:
            self.export_to_json(enriched_videos)
        if choice in ['2', '4']:
            self.export_to_csv(enriched_videos)
        if choice in ['3', '4']:
            self.generate_markdown_report(enriched_videos)

        print("🎉 分析完成！")

    def _display_video_info(self, video: Dict[str, Any], rank: int):
        """显示视频信息"""
        print(f"\n【第{rank}位】{video['title']}")
        print(f"   👤 UP主: {video['owner_name']} | 📺 分区: {video.get('tname', '未知')}")
        print(
            f"   📊 播放: {self.format_number(video['play_count'])} | 弹幕: {self.format_number(video['danmaku_count'])} | 点赞: {self.format_number(video['like_count'])}")
        print(
            f"   🪙 投币: {self.format_number(video['coin_count'])} | 收藏: {self.format_number(video['favorite_count'])} | 转发: {self.format_number(video['share_count'])}")
        print(f"   🔗 BV号: {video['bvid']}")
        print(f"   🕒 时长: {video['duration_formatted']} | 发布时间: {video['publish_time']}")
        print("-" * 60)


def main():
    """主函数"""
    analyzer = BilibiliPopularVideoAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
