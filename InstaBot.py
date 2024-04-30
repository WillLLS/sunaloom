import requests
import json
import time

class InstaBot():
    
    headers = {
        "Host": "www.instagram.com",
        "scheme": "https",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Ig-App-Id": "1217981644879628",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    

    
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        
        with open("cookies.json", "r") as f:
            self.cookies = json.load(f)
        
        self.headers["X-Csrftoken"] = self.cookies["csrftoken"]
        
        self.session = requests.Session()
        self.session.cookies.update(self.cookies)
        
        self._user_id = self.get_user_id(username)
    
    def get_user_id(self, username):
        headers = self.headers.copy()
        
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        headers["X-Fb-Friendly-Name"] = "PolarisProfilePageQuery"
        
        res = self.session.get(url, headers=headers)
        data = res.json()     
        
        if data["status"] == "ok":
            return res.json()["data"]["user"]["id"]
        else:
            raise Exception("Error getting the user id")
             
    def get_user_medias(self, username, count=12):
        
        url = "https://www.instagram.com/api/graphql"
        
        headers = self.headers.copy()
        headers["X-Fb-Friendly-Name"] = "PolarisProfilePostsQuery"
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        variables = {
            "data": {
                "count": count,
                "include_relationship_info": True,
                "latest_besties_reel_media": True,
                "latest_reel_media": True
            },
            "username": username,
            "__relay_internal__pv__PolarisShareMenurelayprovider": False
        }

        payload = {
            "fb_dtsg": "NAcN4mcz7mVvV9Vam_AbSqv2wLq0odnPlCv6kXXIUax-M6s7dZtKj0Q:17843669410156967:1707097413",
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "PolarisProfilePostsQuery",
            "variables": json.dumps(variables),
            "doc_id": "7667453073311120",
        }
        

        res = self.session.post(url, headers=headers, data=payload)
        edges = res.json()["data"]["xdt_api__v1__feed__user_timeline_graphql_connection"]["edges"]
        pks = [edges[i]["node"]["pk"] for i in range(len(edges))]
        codes = [edges[i]["node"]["code"] for i in range(len(edges))]
        
        print("Media ID:", pks)
        
        return pks, codes
    
    def get_info_follow(self, user_id):
        
        url = f"https://www.instagram.com/api/v1/friendships/show/{user_id}/"
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        payload = {
            "container_module": "profile",
            "nav_chain": "PolarisProfilePostsTabRoot:profilePage:1:via_cold_start",
            "user_id": user_id
        }
        
        res = self.session.get(url, headers=headers, data=payload)
        
        data = res.json()
        print(data)
        if data["status"] == "ok":
            
            return data["following"]
        
        else:
            raise Exception("Error getting info follow")
    
    def follow_user(self, user_id):
        
        url = f"https://www.instagram.com/api/v1/friendships/create/{user_id}/"
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        payload = {
            "container_module": "profile",
            "nav_chain": "PolarisProfilePostsTabRoot:profilePage:1:via_cold_start",
            "user_id": user_id
        }
        
        res = self.session.post(url, headers=headers, data=payload)
        
        data = res.json()
        
        if data["status"] == "ok":
            return 1
        else:
            raise Exception("Error following the user")
        
    def unfollow_user(self, user_id):
        url = f"https://www.instagram.com/api/v1/friendships/destroy/{user_id}/"
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        payload = {
            "container_module": "profile",
            "nav_chain": "PolarisProfilePostsTabRoot:profilePage:1:via_cold_start",
            "user_id": user_id
        }
        
        res = self.session.post(url, headers=headers, data=payload)
        data = res.json()
        
        if data["status"] == "ok":
            return 1
        else:
            raise Exception("Error unfollowing the user")
    
    def get_following(self):
        url = f"https://www.instagram.com/api/v1/friendships/{self._user_id}/following/?count=12"
            
        res = self.session.get(url, headers=self.headers)
        data = res.json()
        
        following = []

        for user_info in data["users"]:
            user = {
                    "username": user_info["username"],
                    "id": user_info["pk"]
                }
            following.append(user)

        while "next_max_id" in list(data.keys()):
            
            url = f"https://www.instagram.com/api/v1/friendships/{self._user_id}/following/?count=24&max_id={data['next_max_id']}"
            res = self.session.get(url, headers=self.headers)
            data = res.json()
            
            for user_info in data["users"]:
                user = {
                    "username": user_info["username"],
                    "id": user_info["pk"]
                }
                following.append(user)

        return following
    
    def get_followers(self):
        
        url = f"https://www.instagram.com/api/v1/friendships/{self._user_id}/followers/?count=12"
        
        res = self.session.get(url, headers=self.headers)
        data = res.json()

        followers = []

        for user_info in data["users"]:
            user = {
                    "username": user_info["username"],
                    "id": user_info["pk"]
                }
            followers.append(user)

        while "next_max_id" in list(data.keys()):
            
            url = f"https://www.instagram.com/api/v1/friendships/{self._user_id}/followers/?count=12&max_id={data['next_max_id']}"
            res = self.session.get(url, headers=self.headers)
            data = res.json()

            for user_info in data["users"]:
                user = {
                        "username": user_info["username"],
                        "id": user_info["pk"]
                    }
                followers.append(user)
                
        return followers
    
    def like_media(self, media_id):
        url = 'https://www.instagram.com/graphql/query'
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        variables = {
            "media_id": media_id,
        }

        payload = {
            'fb_dtsg': 'NAcN4mcz7mVvV9Vam_AbSqv2wLq0odnPlCv6kXXIUax-M6s7dZtKj0Q:17843669410156967:1707097413',
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'usePolarisLikeMediaLikeMutation',
            'variables': json.dumps(variables),
            'doc_id': '5788782404552294'
        }
        
        response = self.session.post(url, headers=headers, data=payload)
        
        data = response.json()
        
        if data["status"] == "ok":
            return 1
        else:
            raise Exception("Error following the user")
    
    def unlike_media(self, media_id):
        url = 'https://www.instagram.com/graphql/query'
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        variables = {
            "media_id": media_id,
        }

        payload = {
            'fb_dtsg': 'NAcN4mcz7mVvV9Vam_AbSqv2wLq0odnPlCv6kXXIUax-M6s7dZtKj0Q:17843669410156967:1707097413',
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'usePolarisUnLikeMediaLikeMutation',
            'variables': json.dumps(variables),
            'doc_id': '9340949795922633'
        }
        
        response = self.session.post(url, headers=headers, data=payload)
        
        data = response.json()
        
        if data["status"] == "ok":
            return 1
        else:
            raise Exception("Error following the user")
    
    def comment_media(self, media_id, comment):
        
        url = "https://www.instagram.com/graphql/query"
        
        headers = self.headers.copy()
        headers["X-Fb-Friendly-Name"] = "PolarisProfilePostsQuery"
        
        connection = "client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection(data:{},media_id:\"" \
                + media_id \
                + "\",sort_order:\"popular\")"
        
        variables = {
            "connections": [connection],
            "request_data":{"comment_text":comment},"media_id":media_id
        }

        payload = {
            "fb_dtsg": "NAcM9DGkulbdckKN7KoYzcYuDVrEgYsIpD0cH-K_3vQSFVtibMLezAg:17843669410156967:1707097413",
            "fb_api_req_friendly_name": "PolarisPostCommentInputRevampedMutation",
            "variables": json.dumps(variables),
            "doc_id": "7401025399932973"
        }
        
        res = self.session.post(url, headers=headers, data=payload)
        
        data = res.json()
        
        if data["status"] == "ok":
            return 1
        else:
            raise Exception("Error following the user")
                
    def post_story(self, image_path):
        
        headers = self.headers.copy()
        
        
        id = str(int(time.time() * 1000))
        X_entity_name = "fb_uploader_" + id
        
        url = f"https://i.instagram.com/rupload_igphoto/{X_entity_name}"
        
        with open(image_path, "rb") as img:
            image = img.read()
            
        img_length = str(len(image))  
        
        from PIL import Image
        width = Image.open(image_path).width
        height = Image.open(image_path).height
        
        Rupload_Params = {
            "media_type": 1,
            "upload_id": id,
            "upload_media_height": height,
            "upload_media_width": width
        }
        
        headers["Host"] = "i.instagram.com"
        headers["Content-Type"] = "image/jpeg"
        headers["X-Entity-Length"] = img_length
        headers["X-Entity-Name"] = X_entity_name
        headers["Offset"] = '0'
        headers["X-Entity-Type"] = "image/jpeg"
        headers["X-Instagram-Rupload-Params"] = json.dumps(Rupload_Params)
        
        res = self.session.post(url, headers=headers, data=open(image_path, "rb").read())
        
        data = res.json()
        
        if data["status"] != "ok":
            raise Exception("Error uploading the image")
            return
        
        ##  Configure to story
        headers = self.headers.copy()
        
        url = "https://www.instagram.com/api/v1/web/create/configure_to_story/"
        
        headers["Host"] = "www.instagram.com"
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        payload = {
            "caption": "",
            "upload_id": id
        }
        
        res = self.session.post(url, headers=headers, data=payload)
        data = res.json()
        
        if data["status"] != "ok":
            raise Exception("Error configuring the story")

        return data["mdeia"]["id"]



if __name__ == "__main__":
    import os
    if not os.path.exists("data"):
        os.mkdir("data")
        
    if not os.path.exists("horoscopes"):
        os.mkdir("horoscopes")
        
    if not os.path.exists("posts_api"):
        os.mkdir("posts_api")
        
    if not os.path.exists("posts"):
        os.mkdir("posts")
        
    if not os.path.exists("stories"):
        os.mkdir("stories")
    
    bot = InstaBot("horoscope_fr_")
    id = bot.get_user_id("williamlls")
    #pks_medias, codes_medias = bot.get_user_medias("williamlls")
    
    bot.post_story("balance.jpg")
    #bot.like_media(pks_medias[-1])
    #bot.comment_media(pks_medias[-1], comment="Nice pic")
    
