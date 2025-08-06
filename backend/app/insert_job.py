from datetime import datetime
from app import create_app, db
from app.models.job import Job

def insert_jobs():
    app = create_app()
    with app.app_context():
        jobs_data = [
            # 技术类
            {"title": "后端开发工程师", "category": "技术", "min": 12000, "max": 20000, "city": "上海", "address": "上海市浦东新区软件园路88号"},
            {"title": "前端开发工程师", "category": "技术", "min": 10000, "max": 18000, "city": "北京", "address": "北京市朝阳区互联网大厦9层"},
            {"title": "全栈工程师", "category": "技术", "min": 15000, "max": 22000, "city": "深圳", "address": "深圳市南山区科技园5号楼"},
            {"title": "Java开发工程师", "category": "技术", "min": 13000, "max": 21000, "city": "杭州", "address": "杭州市滨江区高新路128号"},
            {"title": "Python数据工程师", "category": "技术", "min": 14000, "max": 23000, "city": "广州", "address": "广州市天河区信息港路66号"},

            # 运营类
            {"title": "运营专员", "category": "运营", "min": 7000, "max": 12000, "city": "上海", "address": "上海市静安区运营中心3楼"},
            {"title": "新媒体运营", "category": "运营", "min": 8000, "max": 15000, "city": "北京", "address": "北京市海淀区中关村大街10号"},
            {"title": "活动运营", "category": "运营", "min": 9000, "max": 16000, "city": "成都", "address": "成都市高新区创业大道88号"},

            # 市场类
            {"title": "市场推广经理", "category": "市场", "min": 10000, "max": 18000, "city": "南京", "address": "南京市玄武区紫峰路18号"},
            {"title": "品牌专员", "category": "市场", "min": 8000, "max": 14000, "city": "武汉", "address": "武汉市江汉区光谷大道56号"},
            {"title": "市场调研员", "category": "市场", "min": 7000, "max": 13000, "city": "重庆", "address": "重庆市渝中区解放碑CBD办公楼"},

            # 销售类
            {"title": "大客户销售经理", "category": "销售", "min": 15000, "max": 30000, "city": "上海", "address": "上海市黄浦区南京东路200号"},
            {"title": "销售顾问", "category": "销售", "min": 9000, "max": 16000, "city": "广州", "address": "广州市越秀区中山大道88号"},
            {"title": "渠道销售", "category": "销售", "min": 10000, "max": 20000, "city": "苏州", "address": "苏州市园区湖东街9号"},

            # 产品类
            {"title": "产品经理", "category": "产品", "min": 12000, "max": 22000, "city": "深圳", "address": "深圳市南山区创新科技园2号"},
            {"title": "产品助理", "category": "产品", "min": 8000, "max": 14000, "city": "天津", "address": "天津市和平区滨江路88号"},

            # 人事类
            {"title": "人事主管", "category": "人事", "min": 9000, "max": 15000, "city": "成都", "address": "成都市武侯区人力资源大厦10楼"},
            {"title": "招聘专员", "category": "人事", "min": 7000, "max": 12000, "city": "杭州", "address": "杭州市西湖区招聘中心8号楼"},

            # 设计/客服类
            {"title": "UI设计师", "category": "设计", "min": 10000, "max": 18000, "city": "广州", "address": "广州市天河区设计创意园区6栋"},
            {"title": "客服专员", "category": "客服", "min": 6000, "max": 10000, "city": "北京", "address": "北京市丰台区呼叫中心大厦5楼"},
        ]

        for jd in jobs_data:
            job = Job(
                company_id=1,
                job_title=jd["title"],
                job_category=jd["category"],
                salary_min=jd["min"],
                salary_max=jd["max"],
                salary_type="月",
                experience_req="不限",
                education_req="本科",
                location=jd["city"],
                job_nature="全职",
                description=f"{jd['title']}岗位职责描述，适合相关经验候选人。",
                requirements=f"1. 具备岗位相关经验；2. 有团队合作精神；3. 学习能力强。",
                benefits="五险一金，绩效奖金，节日福利",
                publish_date=datetime.utcnow(),
                expire_date=datetime(2025, 12, 31),
                view_count=0,
                apply_count=0,
                status="发布",
                contact_email="hr@company.com",
                contact_phone="13800138000",
                address_detail=jd["address"]
            )
            db.session.add(job)
        db.session.commit()
        print(f"成功插入 {len(jobs_data)} 条岗位数据！")

if __name__ == '__main__':
    insert_jobs()
