export 'document_store_stub.dart'
    if (dart.library.io) 'document_store_native.dart'
    if (dart.library.js_interop) 'document_store_web.dart';
