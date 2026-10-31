import 'package:flutter_test/flutter_test.dart';
import 'package:edunova_admin/src/app/admin_app.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

void main() {
  testWidgets('EduNova Administration affiche la connexion sans session', (tester) async {
    FlutterSecureStorage.setMockInitialValues({});
    await tester.pumpWidget(const EduNovaAdminApp());
    await tester.pumpAndSettle();
    expect(find.text('EduNova Administration'), findsOneWidget);
    expect(find.text('Ouvrir EduNova'), findsOneWidget);
    expect(find.text('Mot de passe'), findsOneWidget);
  });
}
