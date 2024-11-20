from django.test import TestCase
from django.urls import reverse
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError

from .models import Video


class TestHomePageMessage(TestCase):

    def test_app_title_message_shown_on_home_page(self):
        url = reverse("home")
        response = self.client.get(url)
        self.assertContains(response, "Music Videos")


class TestAddVideos(TestCase):

    def test_add_video(self):
        add_video_url = reverse("add_video")

        valid_video = {
            "name": "yoga",
            "url": "https://www.youtube.com/watch?v=4vTJHUDB5ak",
            "notes": "yoga for neck and shoulders",
        }

        # follow=True -> view redirects to video list, follow the redirect
        response = self.client.post(add_video_url, data=valid_video, follow=True)

        # redirect?
        self.assertTemplateUsed("video_collection/video_list.html")

        # does list show new video
        self.assertContains(response, "yoga")
        self.assertContains(response, "https://youtube.com/embed/4vTJHUDB5ak")
        self.assertContains(response, "yoga for neck and shoulders")

        # video count on page is correct
        self.assertContains(response, "1 video")
        self.assertNotContains(response, "1 videos")

        # new video in db
        video_count = Video.objects.count()
        self.assertEqual(1, video_count)

        video = Video.objects.first()
        self.assertEqual("yoga", video.name)
        self.assertEqual("https://www.youtube.com/watch?v=4vTJHUDB5ak", video.url)
        self.assertEqual("yoga for neck and shoulders", video.notes)
        self.assertEqual("4vTJHUDB5ak", video.video_id)

        # add another video -> both present?
        valid_video_2 = {
            "name": "full body workout",
            "url": "https://www.youtube.com/watch?v=IFQmOZqvtWg",
            "notes": "30 minutes of aerobics",
        }

        response = self.client.post(add_video_url, data=valid_video_2, follow=True)
        self.assertTemplateUsed("video_collection/video_list.html")
        self.assertContains(response, "2 videos")

        # video 1
        self.assertContains(response, "yoga")
        self.assertContains(response, "https://youtube.com/embed/4vTJHUDB5ak")
        self.assertContains(response, "yoga for neck and shoulders")

        # video 2
        self.assertContains(response, "full body workout")
        self.assertContains(response, "https://youtube.com/embed/IFQmOZqvtWg")
        self.assertContains(response, "30 minutes of aerobics")

        self.assertEqual(2, Video.objects.count())

        # are both videos on the page? query for video with expected data,
        # get method will raise DoesNotExist error if no match, test will fail
        video_1_in_db = Video.objects.get(
            name="yoga",
            url="https://www.youtube.com/watch?v=4vTJHUDB5ak",
            notes="yoga for neck and shoulders",
            video_id="4vTJHUDB5ak",
        )
        video_2_in_db = Video.objects.get(
            name="full body workout",
            url="https://www.youtube.com/watch?v=IFQmOZqvtWg",
            notes="30 minutes of aerobics",
            video_id="IFQmOZqvtWg",
        )

        videos_in_context = list(response.context["videos"])
        expected_videos_in_context = [video_2_in_db, video_1_in_db]  # sorted by name
        self.assertEqual(expected_videos_in_context, videos_in_context)

    def test_add_video_no_notes_video_added(self):
        add_video_url = reverse("add_video")
        valid_video = {
            "name": "yoga",
            "url": "https://www.youtube.com/watch?v=4vTJHUDB5ak",
        }

        response = self.client.post(add_video_url, data=valid_video, follow=True)
        self.assertTemplateUsed("video_collection/video_list.html")

        self.assertContains(response, "yoga")
        self.assertContains(response, "https://youtube.com/embed/4vTJHUDB5ak")

        self.assertContains(response, "1 video")
        self.assertNotContains(response, "1 videos")

        video_count = Video.objects.count()
        self.assertEqual(1, video_count)

        video = Video.objects.first()
        self.assertContains(response, "yoga")
        self.assertContains(response, "https://youtube.com/embed/4vTJHUDB5ak")
        self.assertEqual("", video.notes)
        self.assertEqual("4vTJHUDB5ak", video.video_id)

    def test_add_video_missing_fields(self):
        add_video_url = reverse("add_video")

        invalid_videos = [
            {
                "name": "",  # no name, should not be allowed
                "url": "https://www.youtube.com/watch?v=4vTJHUDB5ak",
                "notes": "yoga for neck and shoulders",
            },
            {
                # no name field
                "url": "https://www.youtube.com/watch?v=4vTJHUDB5ak",
                "notes": "yoga for neck and shoulders",
            },
            {
                "name": "example",
                "url": "",  # no URL, should not be allowed
                "notes": "yoga for neck and shoulders",
            },
            {
                "name": "example",
                # no URL
                "notes": "yoga for neck and shoulders",
            },
            {
                # no name
                # no URL
                "notes": "yoga for neck and shoulders"
            },
            {
                "name": "",  # blank - not allowed
                "url": "",  # no URL, should not be allowed
                "notes": "yoga for neck and shoulders",
            },
        ]

        for invalid_video in invalid_videos:
            # follow=True not necessary, simple response expected
            response = self.client.post(add_video_url, data=invalid_video)

            self.assertTemplateUsed("video_collection/add_video.html")
            self.assertEqual(0, Video.objects.count())

            messages = response.context["messages"]
            message_texts = [message.message for message in messages]
            self.assertIn("Please check the data entered.", message_texts)

            self.assertContains(response, "Please check the data entered.")

    def test_add_duplicate_video_not_added(self):
        # atomic transaction, keeps changes contained
        # IntegrityError raised -> rollback (separate transaction)
        # therefore, encapsulate the whole transaction in context manager to
        # ensure rollback is complete before we do anything else
        with transaction.atomic():
            new_video = {
                "name": "yoga",
                "url": "https://www.youtube.com/watch?v=4vTJHUDB5ak",
                "notes": "yoga for neck and shoulders",
            }

            Video.objects.create(**new_video)

            video_count = Video.objects.count()
            self.assertEqual(1, video_count)

        with transaction.atomic():
            response = self.client.post(reverse("add_video"), data=new_video)

            self.assertTemplateUsed("video_collection/add.html")

            messages = response.context["messages"]
            message_texts = [message.message for message in messages]
            self.assertIn("You already added that video", message_texts)

            self.assertContains(response, "You already added that video")

        # should still have only 1 video in db
        video_count = Video.objects.count()
        self.assertEqual(1, video_count)

    def test_add_video_invalid_url_not_added(self):
        invalid_video_urls = [
            "https://www.youtube.com/watch",
            "https://www.youtube.com/watch/somethingelse",
            "https://www.youtube.com/watch/somethingelse?v=1234567",
            "https://www.youtube.com/watch?",
            "https://www.youtube.com/watch?abc=123",
            "https://www.youtube.com/watch?v=",
            "https://github.com",
            "12345678",
            "hhhhhhhhttps://www.youtube.com/watch",
            "http://www.youtube.com/watch/somethingelse?v=1234567",
            "https://minneapolis.edu" "https://minneapolis.edu?v=123456" "",
            "    sdfsdf sdfsdf   sfsdfsdf",
            "    https://minneapolis.edu?v=123456     ",
            "[",
            "☂️🌟🌷",
            "!@#$%^&*(",
            "//",
            "file://sdfsdf",
        ]

        for invalid_url in invalid_video_urls:
            new_video = {
                "name": "yoga",
                "url": invalid_url,
                "notes": "yoga for neck and shoulders",
            }

            response = self.client.post(reverse("add_video"), data=new_video)

            self.assertTemplateUsed("video_collection/add.html")

            messages = response.context["messages"]
            message_texts = [message.message for message in messages]
            self.assertIn("Please check the data entered.", message_texts)
            self.assertIn("Invalid YouTube URL", message_texts)

            self.assertContains(response, "Please check the data entered.")
            self.assertContains(response, "Invalid YouTube URL")

            # db should be empty
            video_count = Video.objects.count()
            self.assertEqual(0, video_count)


class TestVideoList(TestCase):

    def test_all_videos_displayed_in_correct_order(self):
        v1 = Video.objects.create(
            name="XYZ", notes="example", url="https://www.youtube.com/watch?v=123"
        )
        v2 = Video.objects.create(
            name="ABC", notes="example", url="https://www.youtube.com/watch?v=456"
        )
        v3 = Video.objects.create(
            name="lmn", notes="example", url="https://www.youtube.com/watch?v=789"
        )
        v4 = Video.objects.create(
            name="def", notes="example", url="https://www.youtube.com/watch?v=101"
        )

        expected_video_order = [v2, v4, v3, v1]
        response = self.client.get(reverse("video_list"))
        videos_in_template = list(response.context["videos"])
        self.assertEqual(expected_video_order, videos_in_template)

    def test_no_video_message(self):
        response = self.client.get(reverse("video_list"))
        videos_in_template = response.context["videos"]
        self.assertContains(response, "No videos")
        self.assertEqual(0, len(videos_in_template))

    def test_video_number_message_single_video(self):
        v1 = Video.objects.create(
            name="XYZ", notes="example", url="https://www.youtube.com/watch?v=123"
        )
        response = self.client.get(reverse("video_list"))
        self.assertContains(response, "1 video")
        self.assertNotContains(response, "1 videos")  # "1 videos" contains "1 video"

    def test_video_number_message_multiple_videos(self):
        v1 = Video.objects.create(
            name="XYZ", notes="example", url="https://www.youtube.com/watch?v=123"
        )
        v2 = Video.objects.create(
            name="ABC", notes="example", url="https://www.youtube.com/watch?v=456"
        )
        v3 = Video.objects.create(
            name="uvw", notes="example", url="https://www.youtube.com/watch?v=789"
        )
        v4 = Video.objects.create(
            name="def", notes="example", url="https://www.youtube.com/watch?v=101"
        )

        response = self.client.get(reverse("video_list"))
        self.assertContains(response, "4 videos")

    def test_video_search_matches(self):
        v1 = Video.objects.create(
            name="ABC", notes="example", url="https://www.youtube.com/watch?v=456"
        )
        v2 = Video.objects.create(
            name="nope", notes="example", url="https://www.youtube.com/watch?v=789"
        )
        v3 = Video.objects.create(
            name="abc", notes="example", url="https://www.youtube.com/watch?v=123"
        )
        v4 = Video.objects.create(
            name="hello aBc!!!",
            notes="example",
            url="https://www.youtube.com/watch?v=101",
        )

        expected_video_order = [v1, v3, v4]
        response = self.client.get(reverse("video_list") + "?search_term=abc")
        videos_in_template = list(response.context["videos"])
        self.assertEqual(expected_video_order, videos_in_template)

    def test_video_search_no_matches(self):
        v1 = Video.objects.create(
            name="ABC", notes="example", url="https://www.youtube.com/watch?v=456"
        )
        v2 = Video.objects.create(
            name="nope", notes="example", url="https://www.youtube.com/watch?v=789"
        )
        v3 = Video.objects.create(
            name="abc", notes="example", url="https://www.youtube.com/watch?v=123"
        )
        v4 = Video.objects.create(
            name="hello aBc!!!",
            notes="example",
            url="https://www.youtube.com/watch?v=101",
        )

        expected_video_order = []
        response = self.client.get(reverse("video_list") + "?search_term=kittens")
        videos_in_template = list(response.context["videos"])
        self.assertEqual(expected_video_order, videos_in_template)
        self.assertContains(response, "No videos")


class TestVideoModel(TestCase):

    def test_create_id(self):
        video = Video.objects.create(
            name="example", url="https://www.youtube.com/watch?v=IODxDxX7oi4"
        )
        self.assertEqual("IODxDxX7oi4", video.video_id)

    def test_create_id_valid_url_with_time_parameter(self):
        # video may have timestamp in query
        video = Video.objects.create(
            name="example", url="https://www.youtube.com/watch?v=IODxDxX7oi4&ts=14"
        )
        self.assertEqual("IODxDxX7oi4", video.video_id)

    def test_create_video_notes_optional(self):
        v1 = Video.objects.create(
            name="example", url="https://www.youtube.com/watch?v=67890"
        )
        v2 = Video.objects.create(
            name="different example",
            notes="example",
            url="https://www.youtube.com/watch?v=12345",
        )
        expected_videos = [v1, v2]
        database_videos = Video.objects.all()
        self.assertCountEqual(expected_videos, database_videos)

    def test_invalid_urls_raise_validation_error(self):
        invalid_video_urls = [
            "https://www.youtube.com/watch",
            "https://www.youtube.com/watch/somethingelse",
            "https://www.youtube.com/watch/somethingelse?v=1234567",
            "https://www.youtube.com/watch?",
            "https://www.youtube.com/watch?abc=123",
            "https://www.youtube.com/watch?v=",
            "https://www.youtube.com/watch?v1234",
            "https://github.com",
            "12345678",
            "hhhhhhhhttps://www.youtube.com/watch",
            "http://www.youtube.com/watch/somethingelse?v=1234567",
            "https://minneapolis.edu" "https://minneapolis.edu?v=123456" "",
        ]

        for invalid_url in invalid_video_urls:
            with self.assertRaises(ValidationError):
                Video.objects.create(
                    name="example", url=invalid_url, notes="example notes"
                )

        video_count = Video.objects.count()
        self.assertEqual(0, video_count)

    def test_duplicate_video_raises_integrity_error(self):
        Video.objects.create(
            name="example", url="https://www.youtube.com/watch?v=IODxDxX7oi4"
        )
        with self.assertRaises(IntegrityError):
            Video.objects.create(
                name="example", url="https://www.youtube.com/watch?v=IODxDxX7oi4"
            )


class TestVideoDetail(TestCase):

    def test_detail_page_displays_all_data(self):
        video_data = {
            "name": "star wars cerveza cristal 1",
            "url": "https://www.youtube.com/watch?v=5hfRjN3txdM",
            "notes": "comercial",
        }

        Video.objects.create(**video_data)

        url = reverse("video_detail", args=[1])

        response = self.client.get(url)

        self.assertTemplateUsed(response, "video_collection/video_detail.html")

        self.assertContains(response, "star wars cerveza cristal 1")
        self.assertContains(response, "https://youtube.com/embed/5hfRjN3txdM")
        self.assertContains(response, "comercial")

    def test_detail_for_invalid_video_returns_404(self):
        # 4 should be an invalid pk, so we should get 404
        url = reverse("video_detail", args=[4])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
