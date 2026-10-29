import 'package:dio/dio.dart';

class ApiClient {
  ApiClient({Dio? dio}) : dio = dio ?? Dio(BaseOptions(
    baseUrl: const String.fromEnvironment('EDUNOVA_API_BASE_URL', defaultValue: 'http://localhost:8000'),
    connectTimeout: const Duration(seconds: 12),
    receiveTimeout: const Duration(seconds: 20),
    headers: const {'Accept': 'application/json'},
  ));

  final Dio dio;
}
