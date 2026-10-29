import 'package:flutter_test/flutter_test.dart';
import 'package:edunova_admin/src/app/admin_app.dart';
void main(){testWidgets('EduNova Studio affiche la connexion',(tester)async{await tester.pumpWidget(const EduNovaAdminApp());expect(find.text('EduNova Studio'),findsOneWidget);expect(find.text('Ouvrir le studio'),findsOneWidget);});}
