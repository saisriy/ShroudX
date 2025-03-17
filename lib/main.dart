import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Image Steganography',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: StegoHomePage(),
    );
  }
}

class StegoHomePage extends StatefulWidget {
  @override
  _StegoHomePageState createState() => _StegoHomePageState();
}

class _StegoHomePageState extends State<StegoHomePage> {
  File? coverImage;
  File? secretImage;
  String? stegoImagePath;
  String? decodedImagePath;

  final String flaskUrl = 'http://172.31.72.202:5000'; // Replace with your Flask server URL

  Future<void> pickImage(bool isCover) async {
    try {
      final pickedFile = await ImagePicker().pickImage(
        source: ImageSource.gallery,
        imageQuality: 85, // Reduce size for faster upload
      );

      if (pickedFile != null) {
        setState(() {
          if (isCover) {
            coverImage = File(pickedFile.path);
          } else {
            secretImage = File(pickedFile.path);
          }
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error picking image: $e')),
      );
    }
  }

  Future<void> encodeImage() async {
    if (coverImage == null || secretImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please select both images first!')),
      );
      return;
    }

    try {
      var request = http.MultipartRequest("POST", Uri.parse("$flaskUrl/encode"));
      request.files.add(await http.MultipartFile.fromPath('cover_image', coverImage!.path));
      request.files.add(await http.MultipartFile.fromPath('secret_image', secretImage!.path));

      var response = await request.send();
      var responseData = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        var jsonData = jsonDecode(responseData);
        setState(() {
          stegoImagePath = "$flaskUrl/outputs/stego.png";
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Encoding complete!')),
        );
      } else {
        throw Exception("Failed to encode image");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error encoding image: $e')),
      );
    }
  }

  Future<void> decodeImage() async {
    try {
      var response = await http.post(Uri.parse("$flaskUrl/decode"));

      if (response.statusCode == 200) {
        var jsonData = jsonDecode(response.body);
        setState(() {
          decodedImagePath = "$flaskUrl/output/decoded.png";
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Decoding complete!')),
        );
      } else {
        throw Exception("Failed to decode image");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error decoding image: $e')),
      );
    }
  }

  Widget buildImagePreview(String? imageUrl) {
    return imageUrl != null
        ? Image.network(
      imageUrl,
      width: 200,
      height: 200,
      loadingBuilder: (context, child, loadingProgress) {
        if (loadingProgress == null) return child;
        return Center(child: CircularProgressIndicator());
      },
      errorBuilder: (context, error, stackTrace) {
        return Text('Failed to load image');
      },
    )
        : Container();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Image Steganography")),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                Column(
                  children: [
                    coverImage != null
                        ? Image.file(coverImage!, width: 100, height: 100)
                        : Icon(Icons.image, size: 100),
                    ElevatedButton(
                      onPressed: () => pickImage(true),
                      child: Text("Pick Cover Image"),
                    ),
                  ],
                ),
                Column(
                  children: [
                    secretImage != null
                        ? Image.file(secretImage!, width: 100, height: 100)
                        : Icon(Icons.image, size: 100),
                    ElevatedButton(
                      onPressed: () => pickImage(false),
                      child: Text("Pick Secret Image"),
                    ),
                  ],
                ),
              ],
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: encodeImage,
              child: Text("Encode Image"),
            ),
            SizedBox(height: 20),
            stegoImagePath != null
                ? Column(
              children: [
                buildImagePreview(stegoImagePath),
                ElevatedButton(
                  onPressed: decodeImage,
                  child: Text("Decode Image"),
                ),
              ],
            )
                : Container(),
            SizedBox(height: 20),
            buildImagePreview(decodedImagePath),
          ],
        ),
      ),
    );
  }
}
