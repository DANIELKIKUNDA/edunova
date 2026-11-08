import 'package:flutter/material.dart';
import '../editorial/editorial_api.dart';

class PlatformShell extends StatefulWidget {
  final EditorialApi api;
  final VoidCallback onLogout;
  const PlatformShell({super.key, required this.api, required this.onLogout});
  @override State<PlatformShell> createState()=>_PlatformShellState();
}

class _PlatformShellState extends State<PlatformShell>{
  Map<String,dynamic>? me,dashboard, institutionStatistics, auditEvents, supportTickets; List<dynamic>? members, institutionControls, institutionDirectory, selectedAdministrators; String? selectedInstitutionId; bool busy=true, directoryBusy=false; String? error, directoryError; int directoryOffset=0,directoryTotal=0; static const int directoryPageSize=25; String directorySearch='',directoryState=''; final directorySearchController=TextEditingController(); int directoryRequestId=0;
  static const roleNames={
    'owner':'Propriétaire de la plateforme','platform_admin':'Administrateur de la plateforme',
    'finance_commercial':'Responsable financier et commercial','content_editorial':'Responsable contenu et éditorial',
    'support_operator':'Opérateur d’assistance','security_audit':'Responsable sécurité et audit',
    'read_only_analyst':'Analyste en lecture seule',
  };
  static const sectionNames={
    'universities':'Universités','users':'Utilisateurs','premium':'Premium','revenue':'Revenus','growth':'Croissance',
    'platform_health':'Santé plateforme','security_alerts':'Alertes sécurité','institutions':'Institutions','accounts':'Comptes',
    'configuration':'Configuration','operations':'Opérations','incidents':'Incidents','payments':'Paiements',
    'campus_licenses':'Licences Campus','settlements':'Règlements','reconciliation':'Rapprochement','drafts':'Brouillons',
    'reviews':'Révisions','publications':'Publications','sources':'Sources','ocr':'OCR','editorial_backlog':'Backlog éditorial',
    'tickets':'Tickets','service_status':'État des services','diagnostics':'Diagnostics','escalations':'Escalades',
    'risky_sessions':'Sessions à risque','security_events':'Événements sécurité','audit_ledger':'Journal d’audit','mfa':'MFA',
    'revocations':'Révocations','alerts':'Alertes','global_kpis':'KPI globaux','cohorts':'Cohortes','trends':'Tendances',
    'usage':'Utilisation','reports':'Rapports',
  };
  @override void initState(){super.initState();load();}
  @override void dispose(){directoryRequestId++;directorySearchController.dispose();super.dispose();}
  Future<void> loadDirectory({int? offset,String? search,String? state})async{
    if(directoryBusy)return;
    final nextOffset=offset??directoryOffset;
    final nextSearch=search??directorySearch;
    final nextState=state??directoryState;
    final request=++directoryRequestId;
    setState((){directoryBusy=true;directoryError=null;});
    try{
      final result=await widget.api.platformInstitutionDirectory(limit:directoryPageSize,offset:nextOffset,search:nextSearch,state:nextState);
      if(!mounted||request!=directoryRequestId)return;
      setState((){institutionDirectory=(result['items'] as List).cast<dynamic>();directoryTotal=result['total'] as int;directoryOffset=nextOffset;directorySearch=nextSearch;directoryState=nextState;directoryBusy=false;});
    }on StudioApiException catch(e){if(mounted&&request==directoryRequestId)setState((){directoryError=e.code;directoryBusy=false;});}
    catch(_){if(mounted&&request==directoryRequestId)setState((){directoryError='Chargement impossible';directoryBusy=false;});}
  }
  Future<void> load()async{setState((){busy=true;error=null;});try{final m=await widget.api.platformMe();final d=await widget.api.platformDashboard();List<dynamic>? roster; if ((m['permissions'] as List?)?.contains('platform.roles.manage') == true) { roster=await widget.api.platformMembers(); } List<dynamic>? controls; Map<String,dynamic>? directory; if ((m['permissions'] as List?)?.contains('platform.institutions.read') == true) { controls=await widget.api.platformInstitutionControls(); directory=await widget.api.platformInstitutionDirectory(limit:directoryPageSize,offset:0); } Map<String,dynamic>? stats, audit, tickets;
    if ((m['permissions'] as List?)?.contains('platform.analytics.read') == true) {stats=await widget.api.platformInstitutionStatistics();}
    if ((m['permissions'] as List?)?.contains('platform.audit.read') == true) {audit=await widget.api.platformAuditEvents();}
    if ((m['permissions'] as List?)?.contains('platform.support.read') == true) {tickets=await widget.api.platformSupportTickets();}
    if(mounted)setState((){institutionStatistics=stats;auditEvents=audit;supportTickets=tickets;me=m;dashboard=d;members=roster;institutionControls=controls;institutionDirectory=(directory?['items'] as List?)?.cast<dynamic>();directoryTotal=(directory?['total'] as int?)??0;directoryOffset=0;busy=false;});}on StudioApiException catch(e){if(mounted)setState((){error=e.statusCode==403?'Accès plateforme non autorisé.':e.code;busy=false;});}catch(_){if(mounted)setState((){error='Impossible de charger le centre de contrôle.';busy=false;});}}
  Future<void> manageMember([Map<String,dynamic>? current]) async {
    final idController=TextEditingController(text:current?['account_id']?.toString()??'');
    String role=current?['role']?.toString()??'read_only_analyst';
    final result=await showDialog<String>(context:context,builder:(dialogContext)=>StatefulBuilder(builder:(dialogContext,setDialogState)=>AlertDialog(
      title:Text(current==null?'Ajouter un membre':'Modifier un membre'),
      content:Column(mainAxisSize:MainAxisSize.min,children:[
        TextField(controller:idController,enabled:current==null,decoration:const InputDecoration(labelText:'Identifiant du compte')),
        const SizedBox(height:12),
        DropdownButtonFormField<String>(initialValue:role,isExpanded:true,items:roleNames.entries.map((e)=>DropdownMenuItem(value:e.key,child:Text(e.value,overflow:TextOverflow.ellipsis))).toList(),onChanged:(value){if(value!=null)setDialogState(()=>role=value);}),
        if(role=='owner')const Padding(padding:EdgeInsets.only(top:12),child:Text('Rôle propriétaire : accès sensible réservé à la direction Volcano Tech. Vérifiez l’identité du bénéficiaire.')),
        if(current!=null)const Padding(padding:EdgeInsets.only(top:12),child:Text('Les changements utilisent la version du serveur pour éviter les écrasements concurrents.')),
      ]),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialogContext),child:const Text('Annuler')),
        if(current!=null&&current['active']==true)TextButton(onPressed:()=>Navigator.pop(dialogContext,'deactivate'),child:const Text('Désactiver')),
        FilledButton(onPressed:()=>Navigator.pop(dialogContext,'grant'),child:const Text('Enregistrer'))],
    )));
    final id=idController.text.trim();idController.dispose();
    if(!mounted||result==null)return;
    if(id.isEmpty){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Identifiant obligatoire.')));return;}
    if(result=='deactivate'){
      final confirmed=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Confirmer la désactivation'),content:Text('Désactiver l’accès plateforme du compte $id ?'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Annuler')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Confirmer'))]));
      if(confirmed!=true||!mounted)return;
    }
    try{
      if(result=='deactivate'){await widget.api.deactivatePlatformMember(id,current!['row_version'] as int);}
      else{await widget.api.grantPlatformMember(id,role,expectedVersion:current?['row_version'] as int?);}
      if(!mounted)return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Gouvernance mise à jour.')));
      await load();
    }on StudioApiException catch(e){
      if(!mounted)return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.isConflict?'Conflit de version : actualisez la liste avant de réessayer.':e.statusCode==403?'Permission refusée par le serveur.':e.code)));
      if(e.isConflict)await load();
    }catch(_){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Modification impossible. Réessayez.')));}
  }
  Future<void> manageInstitution([Map<String,dynamic>? current]) async {
    final idController=TextEditingController(text:current?['institution_id']?.toString()??'');
    final reasonController=TextEditingController();
    String state=current?['state']?.toString()=='suspended'?'active':'suspended';
    final approved=await showDialog<bool>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setLocal)=>AlertDialog(
      title:Text(current==null?'Contrôler un établissement existant':'Changer le statut institutionnel'),
      content:Column(mainAxisSize:MainAxisSize.min,children:[
        TextField(controller:idController,enabled:current==null,decoration:const InputDecoration(labelText:'Identifiant institutionnel')),
        DropdownButtonFormField<String>(initialValue:state,items:const[DropdownMenuItem(value:'active',child:Text('Actif')),DropdownMenuItem(value:'suspended',child:Text('Suspendu'))],onChanged:(v){if(v!=null)setLocal(()=>state=v);}),
        TextField(controller:reasonController,maxLength:500,maxLines:3,decoration:const InputDecoration(labelText:'Motif obligatoire (10 caractères minimum)')),
        const Text('Décision auditée ; ne donne aucun accès aux données privées.'),
      ]),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Annuler')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Confirmer'))],
    )));
    final id=idController.text.trim(),reason=reasonController.text.trim();idController.dispose();reasonController.dispose();
    if(approved!=true||!mounted)return;
    if(id.isEmpty||reason.length<10){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Identifiant et motif de 10 caractères minimum requis.')));return;}
    try {await widget.api.changePlatformInstitutionControl(id,state,reason,expectedVersion:current?['row_version'] as int?);if(mounted){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Décision enregistrée.')));await load();}}
    on StudioApiException catch(e){if(mounted){ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.isConflict?'Conflit de version : actualisation nécessaire.':e.code)));if(e.isConflict)await load();}}
    catch(_){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Opération impossible.')));}
  }
  Future<void> loadAdministrators(String institutionId) async {
    try {final rows=await widget.api.platformInstitutionAdministrators(institutionId);
      if(mounted)setState((){selectedInstitutionId=institutionId;selectedAdministrators=rows;});
    }on StudioApiException catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.code)));}
  }
  Future<void> assignAdministrator() async {
    final institutionId=selectedInstitutionId;if(institutionId==null)return;
    final account=TextEditingController();String role='admin';
    final accepted=await showDialog<bool>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,update)=>AlertDialog(
      title:const Text('Inviter un administrateur institutionnel'),content:Column(mainAxisSize:MainAxisSize.min,children:[
        TextField(controller:account,decoration:const InputDecoration(labelText:'Identifiant du compte existant')),
        DropdownButton<String>(value:role,items:const[DropdownMenuItem(value:'admin',child:Text('Administrateur')),DropdownMenuItem(value:'academic_admin',child:Text('Administrateur académique')),DropdownMenuItem(value:'faculty_admin',child:Text('Administrateur de faculté'))],onChanged:(value){if(value!=null)update(()=>role=value);}),
        const Text('L’invitation devra être acceptée dans le parcours institutionnel. Aucun accès aux données privées n’est accordé par le centre Volcano Tech.'),
      ]),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Annuler')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Inviter'))])));
    final id=account.text.trim();account.dispose();if(accepted!=true||id.isEmpty||!mounted)return;
    try {await widget.api.platformAssignAdministrator(institutionId,id,role);await loadAdministrators(institutionId);}
    on StudioApiException catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.isConflict?'Conflit de version : rechargez les affectations.':e.code)));}
  }
  Future<void> revokeAdministrator(Map<String,dynamic> member) async {
    final institutionId=selectedInstitutionId;if(institutionId==null)return;
    final confirmed=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Révoquer cet accès ?'),content:Text('Compte : ${member['account_id']}'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Annuler')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Révoquer'))]));
    if(confirmed!=true||!mounted)return;
    try{await widget.api.platformRevokeAdministrator(institutionId,member['account_id'].toString(),member['row_version'] as int);await loadAdministrators(institutionId);}
    on StudioApiException catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.code)));}
  }
  Future<void> createSupportTicket() async {
    final institution=TextEditingController(),title=TextEditingController(),description=TextEditingController();
    final accepted=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Nouveau ticket de support'),content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[TextField(controller:institution,decoration:const InputDecoration(labelText:'Identifiant université')),TextField(controller:title,decoration:const InputDecoration(labelText:'Objet')),TextField(controller:description,maxLines:3,decoration:const InputDecoration(labelText:'Description technique (sans données étudiantes)'))])),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Annuler')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Créer'))]));
    final id=institution.text.trim(),name=title.text.trim(),detail=description.text.trim();institution.dispose();title.dispose();description.dispose();
    if(accepted!=true||!mounted)return;
    try{await widget.api.platformCreateSupportTicket(id,name,detail,'normal');final data=await widget.api.platformSupportTickets();if(mounted)setState(()=>supportTickets=data);}
    on StudioApiException catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.code)));}
  }
  Future<void> advanceTicket(Map<String,dynamic> ticket) async {
    final next=switch(ticket['state']){'open'=>'in_progress','in_progress'=>'resolved','resolved'=>'closed',_=>null};if(next==null)return;
    try{await widget.api.platformUpdateSupportTicket(ticket['id'].toString(),next,ticket['row_version'] as int,assignedTo:ticket['assigned_to'] as String?);final data=await widget.api.platformSupportTickets();if(mounted)setState(()=>supportTickets=data);}
    on StudioApiException catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.code)));}
  }
  IconData iconFor(String s){if(s.contains('security')||s=='mfa'||s=='revocations')return Icons.security_rounded;if(s.contains('revenue')||s.contains('payment')||s.contains('license')||s.contains('reconciliation')||s=='settlements')return Icons.account_balance_wallet_rounded;if(s.contains('institution')||s=='universities')return Icons.account_balance_rounded;if(s.contains('content')||s=='drafts'||s=='reviews'||s=='publications'||s=='sources')return Icons.auto_stories_rounded;if(s.contains('ticket')||s.contains('incident')||s=='diagnostics'||s=='escalations')return Icons.support_agent_rounded;if(s.contains('health')||s=='operations')return Icons.monitor_heart_rounded;return Icons.analytics_rounded;}
  @override Widget build(BuildContext context){final role=(me?['role']??'').toString();final sections=(dashboard?['sections'] as List?)?.cast<String>()??const[];return Scaffold(
    appBar:AppBar(title:Row(children:[Image.asset('assets/branding/edunova_logo_official.png',height:38),const SizedBox(width:12),const Text('EduNova • Centre de contrôle')]),actions:[IconButton(onPressed:load,tooltip:'Actualiser',icon:const Icon(Icons.refresh_rounded)),PopupMenuButton<String>(onSelected:(v){if(v=='logout')widget.onLogout();},itemBuilder:(_)=>const[PopupMenuItem(value:'logout',child:Text('Se déconnecter'))])]),
    body:busy?const Center(child:CircularProgressIndicator()):error!=null?Center(child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,children:[const Icon(Icons.lock_outline_rounded,size:48),const SizedBox(height:12),Text(error!,textAlign:TextAlign.center),const SizedBox(height:16),FilledButton(onPressed:load,child:const Text('Réessayer'))]))):LayoutBuilder(builder:(context,c){final cols=c.maxWidth>=1200?4:c.maxWidth>=760?3:c.maxWidth>=520?2:1;return SingleChildScrollView(padding:const EdgeInsets.all(24),child:Center(child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:1400),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      Text('Bonjour ${widget.api.displayName}',style:Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:6),Text(roleNames[role]??role,style:Theme.of(context).textTheme.titleMedium?.copyWith(color:Theme.of(context).colorScheme.primary,fontWeight:FontWeight.w700)),const SizedBox(height:6),Text('Les modules affichés sont calculés par le serveur selon le principe du moindre privilège.',style:Theme.of(context).textTheme.bodyMedium),const SizedBox(height:24),
      GridView.builder(shrinkWrap:true,physics:const NeverScrollableScrollPhysics(),gridDelegate:SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount:cols,crossAxisSpacing:14,mainAxisSpacing:14,childAspectRatio:1.65),itemCount:sections.length,itemBuilder:(_,i){final s=sections[i];return Card(child:InkWell(borderRadius:BorderRadius.circular(12),onTap:(){ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('${sectionNames[s]??s} — espace sécurisé prêt pour ses données métier.')));},child:Padding(padding:const EdgeInsets.all(18),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Icon(iconFor(s),size:30,color:Theme.of(context).colorScheme.primary),const Spacer(),Text(sectionNames[s]??s,style:Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w800)),const SizedBox(height:4),Text('Accès autorisé',style:Theme.of(context).textTheme.bodySmall)]))));}),
      if(institutionStatistics!=null) ...[
        const SizedBox(height:20),Text('Indicateurs institutionnels',style:Theme.of(context).textTheme.titleLarge),
        Wrap(spacing:12,children:[for(final key in ['total','active','suspended','archived'])
          Chip(label:Text('$key : ${institutionStatistics![key]??0}'))]),
      ],
      if(auditEvents!=null) ...[
        const SizedBox(height:20),Text('Journal des décisions centrales',style:Theme.of(context).textTheme.titleLarge),
        const Text('Événements de gouvernance uniquement, sans données privées ni métadonnées sensibles.'),
        for(final event in (auditEvents!['items'] as List)) ListTile(
          leading:const Icon(Icons.history_rounded),
          title:Text((event['action']??'').toString()),
          subtitle:Text('${event['entity_id']??''} • ${event['occurred_at']??''}')),
      ],
      if(supportTickets!=null) ...[
        const SizedBox(height:24),Row(children:[Expanded(child:Text('Support central',style:Theme.of(context).textTheme.titleLarge)),if((me?['permissions'] as List?)?.contains('platform.support.manage')==true)FilledButton.icon(onPressed:createSupportTicket,icon:const Icon(Icons.add),label:const Text('Ticket'))]),
        Text('${supportTickets!['total']??0} tickets — données opérationnelles uniquement'),
        for(final entry in (supportTickets!['items'] as List)) Card(child:ListTile(title:Text((entry['title']??'').toString()),subtitle:Text('${entry['institution_id']} • ${entry['state']} • ${entry['priority']}'),trailing:(me?['permissions'] as List?)?.contains('platform.support.manage')==true?TextButton(onPressed:()=>advanceTicket(entry as Map<String,dynamic>),child:const Text('Avancer')):null)),
      ],
      if(selectedAdministrators!=null) ...[
        const SizedBox(height:24),Row(children:[Expanded(child:Text('Administrateurs de $selectedInstitutionId',style:Theme.of(context).textTheme.titleLarge)),FilledButton.icon(onPressed:assignAdministrator,icon:const Icon(Icons.person_add),label:const Text('Inviter'))]),
        for(final entry in selectedAdministrators!) Card(child:ListTile(title:Text((entry['account_id']??'').toString()),subtitle:Text('${entry['role']} • ${entry['state']} • version ${entry['row_version']}'),trailing:entry['state']=='revoked'?null:IconButton(onPressed:()=>revokeAdministrator(entry as Map<String,dynamic>),icon:const Icon(Icons.person_remove_outlined),tooltip:'Révoquer'))),
      ],
      if(institutionDirectory!=null) ...[
        const SizedBox(height:24),Text('Annuaire institutionnel',style:Theme.of(context).textTheme.titleLarge),
        const SizedBox(height:8),const Text('Métadonnées institutionnelles uniquement — recherche et pagination côté serveur.'),
        Wrap(spacing:12,runSpacing:8,crossAxisAlignment:WrapCrossAlignment.center,children:[
          SizedBox(width:260,child:TextField(controller:directorySearchController,decoration:const InputDecoration(labelText:'Nom ou identifiant',prefixIcon:Icon(Icons.search)),onSubmitted:(value)=>loadDirectory(offset:0,search:value))),
          DropdownButton<String>(value:directoryState,items:const[DropdownMenuItem(value:'',child:Text('Tous les statuts')),DropdownMenuItem(value:'active',child:Text('Actifs')),DropdownMenuItem(value:'suspended',child:Text('Suspendus')),DropdownMenuItem(value:'archived',child:Text('Archivés'))],onChanged:directoryBusy?null:(value){if(value!=null)loadDirectory(offset:0,state:value);}),
          FilledButton.tonalIcon(onPressed:directoryBusy?null:()=>loadDirectory(offset:0,search:directorySearchController.text),icon:const Icon(Icons.search),label:const Text('Rechercher')),
        ]),
        if(directoryError!=null)Text(directoryError!,style:TextStyle(color:Theme.of(context).colorScheme.error)),
        if(directoryBusy)const LinearProgressIndicator(),
        ...institutionDirectory!.map((entry){final item=entry as Map<String,dynamic>;return Card(child:ListTile(
          leading:const Icon(Icons.account_balance_outlined),
          title:Text((item['name']??'').toString()),
          subtitle:Text('${item['slug']} • ${item['city']??item['country_code']} • ${item['state']}'),
          trailing:Row(mainAxisSize:MainAxisSize.min,children:[if((me?['permissions'] as List?)?.contains('platform.assignments.manage')==true)IconButton(icon:const Icon(Icons.group_outlined),tooltip:'Administrateurs institutionnels',onPressed:()=>loadAdministrators(item['institution_id'].toString())),if((me?['permissions'] as List?)?.contains('platform.institutions.manage')==true)IconButton(icon:const Icon(Icons.admin_panel_settings_outlined),tooltip:'Contrôler cet établissement',
                onPressed:(){final existing=institutionControls?.where((e)=>e is Map && e['institution_id']==item['institution_id']).toList();final control=existing!=null&&existing.isNotEmpty?existing.first as Map<String,dynamic>:null;manageInstitution({'institution_id':item['institution_id'],'state':item['state'],'row_version':control?['row_version']});})
        ]),
        ));}),
      ],
      if(institutionDirectory!=null) ...[
        const SizedBox(height:8),Wrap(spacing:12,crossAxisAlignment:WrapCrossAlignment.center,children:[
          Text('Résultats ${directoryTotal==0?0:directoryOffset+1}–${directoryOffset+institutionDirectory!.length} sur $directoryTotal'),
          OutlinedButton(onPressed:directoryBusy||directoryOffset==0?null:()=>loadDirectory(offset:(directoryOffset-directoryPageSize).clamp(0,directoryTotal)),child:const Text('Précédent')),
          OutlinedButton(onPressed:directoryBusy||directoryOffset+institutionDirectory!.length>=directoryTotal?null:()=>loadDirectory(offset:directoryOffset+directoryPageSize),child:const Text('Suivant')),
        ]),
      ],
      if(institutionControls!=null) ...[
        const SizedBox(height:24),Row(children:[Expanded(child:Text('Contrôle des établissements',style:Theme.of(context).textTheme.titleLarge)),
          if((me?['permissions'] as List?)?.contains('platform.institutions.manage')==true)FilledButton.icon(onPressed:()=>manageInstitution(),icon:const Icon(Icons.add),label:const Text('Contrôler'))]),
        const SizedBox(height:8),const Text('Statut central et motif de décision — aucune donnée académique ou financière exposée.'),
        ...institutionControls!.map((entry){final c=entry as Map<String,dynamic>;return Card(child:ListTile(
          title:Text('${c['institution_id']} • ${c['state']=='active'?'Actif':'Suspendu'}'),
          subtitle:Text('${c['reason']} • version ${c['row_version']}'),
          trailing:(me?['permissions'] as List?)?.contains('platform.institutions.manage')==true?IconButton(icon:const Icon(Icons.edit_outlined),tooltip:'Modifier le statut',onPressed:()=>manageInstitution(c)):null,
        ));}),
      ],
      if(members!=null) ...[const SizedBox(height:24),Row(children:[Expanded(child:Text('Gouvernance des accès Volcano Tech',style:Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.bold))),FilledButton.icon(onPressed:()=>manageMember(),icon:const Icon(Icons.person_add_alt_1),label:const Text('Ajouter'))]),const SizedBox(height:8),Text('Membres de la plateforme uniquement — aucune donnée privée des étudiants ou des universités.'),const SizedBox(height:12),...members!.map((entry){final m=entry as Map<String,dynamic>;final active=m['active']==true;return Card(child:ListTile(leading:Icon(active?Icons.verified_user:Icons.person_off_outlined,color:active?Theme.of(context).colorScheme.primary:Theme.of(context).disabledColor),title:Text((m['account_id']??'').toString()),subtitle:Text('${roleNames[m['role']]??m['role']} • version ${m['row_version']}'),trailing:Row(mainAxisSize:MainAxisSize.min,children:[Text(active?'Actif':'Désactivé'),IconButton(tooltip:'Modifier les droits',icon:const Icon(Icons.edit_outlined),onPressed:()=>manageMember(m))])));})],
      const SizedBox(height:24),Card(child:Padding(padding:const EdgeInsets.all(18),child:Row(children:[const Icon(Icons.verified_user_outlined),const SizedBox(width:12),Expanded(child:Text('${(me?['permissions'] as List?)?.length??0} permissions effectives • rôle et périmètre contrôlés côté API.'))]))),
    ]))));}) );}
}
